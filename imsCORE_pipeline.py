import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
from matplotlib.colors import ListedColormap
import seaborn as sns
import warnings, os, gc, glob
warnings.filterwarnings('ignore')

from pyimzml.ImzMLParser import ImzMLParser 
from sklearn.decomposition import PCA, IncrementalPCA
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans, MiniBatchKMeans
from sklearn.metrics import silhouette_score, silhouette_samples
from scipy.stats import kruskal, mannwhitneyu
from scipy.ndimage import binary_fill_holes, gaussian_filter
import umap 


# ── Palette MSI — couleurs distinctes même pour 20+ clusters (import pour la fonction run_cartes_spatiales()) ─────────────────
from matplotlib.colors import ListedColormap
import matplotlib.cm as mcm



# ══════════════════════════════════════════════════════════════════════════════
# PARAMÈTRES PAR DEFAUT
# ══════════════════════════════════════════════════════════════════════════════

# ── Fichier(s) imzML ──────────────────────────────────────────────────────────
# Chemin unique OU liste OU glob pattern
IMZML_INPUT = 'ratbrain-nor-neg1-root mean square.imzML'          # ← un seul fichier
IMZML_INPUT = ['sample1.imzML', 'sample2.imzML']   # ← liste
# IMZML_INPUT = 'data/*.imzML'                        # ← glob

# ── Fenêtre m/z ───────────────────────────────────────────────────────────────
MZ_MIN      = 600.0
MZ_MAX      = 1000.0
MZ_BIN_SIZE = 0.1

# ── Normalisation & filtrage ──────────────────────────────────────────────────
NORMALIZE_TIC      = True
ION_MIN_PREVALENCE = 0.01
ION_MIN_INTENSITY  = 0.0

# ── Masque tissu ──────────────────────────────────────────────────────────────
AUTO_TISSUE_MASK    = True
TIC_TISSUE_QUANTILE = 0.25

# ── PCA ───────────────────────────────────────────────────────────────────────
N_PCA_COMPONENTS = 15

# ── Bisecting K-Means ─────────────────────────────────────────────────────────
MAX_CLUSTERS         = 20
SILHOUETTE_THRESHOLD = 0.3
MIN_CLUSTER_SIZE     = 30
N_INIT_KMEANS        = 20
RANDOM_STATE         = 42

# ── UMAP ──────────────────────────────────────────────────────────────────────
UMAP_N_NEIGHBORS  = 50
UMAP_MIN_DIST     = 0.05
UMAP_N_COMPONENTS = 2

# ── Export ────────────────────────────────────────────────────────────────────
CSV_PIXELS   = 'bkm_msi_pixels.csv'
CSV_SPECTRA  = 'bkm_msi_spectra_per_cluster.csv'
CSV_PEAKS    = 'bkm_msi_top_peaks.csv'

# ── Analyse PKL ───────────────────────────────────────────────────────────────
max_intensity_size = 4000
CSV_LABEL_RATIOS = "label_ratios.csv"

# ── Dérivés ───────────────────────────────────────────────────────────────────
N_BINS  = int(round((MZ_MAX - MZ_MIN) / MZ_BIN_SIZE))
MZ_AXIS = np.linspace(MZ_MIN, MZ_MAX, N_BINS, endpoint=False)

# Résoudre la liste de fichiers
if isinstance(IMZML_INPUT, str) and '*' in IMZML_INPUT:
    IMZML_FILES = sorted(glob.glob(IMZML_INPUT))
elif isinstance(IMZML_INPUT, str):
    IMZML_FILES = [IMZML_INPUT]
else:
    IMZML_FILES = list(IMZML_INPUT)


# ══════════════════════════════════════════════════════════════════════════════
# IMZML
# ══════════════════════════════════════════════════════════════════════════════


def run_chargement_imzml():
    '''Gere le lancement du programme uniquement lorsque l'utilisateur a fait le choix du fichier imzml et le choix des parametres'''

    # declaration global de variable qui serviront plus tard
    global tic_all, MZ_AXIS, N_BINS, y_max, x_max, coords, n_pixels, n_samples, sample_id, IMZML_FILES, spectra

    # ── Dérivés ───────────────────────────────────────────────────────────────────
    N_BINS  = int(round((MZ_MAX - MZ_MIN) / MZ_BIN_SIZE))
    MZ_AXIS = np.linspace(MZ_MIN, MZ_MAX, N_BINS, endpoint=False)
    # Résoudre la liste de fichiers
    if isinstance(IMZML_INPUT, str) and '*' in IMZML_INPUT:
        IMZML_FILES = sorted(glob.glob(IMZML_INPUT))
    elif isinstance(IMZML_INPUT, str):
        IMZML_FILES = [IMZML_INPUT]
    else:
        IMZML_FILES = list(IMZML_INPUT)

    # Chargement mémoire-efficace de N fichiers imzML
    # Chaque fichier garde son origine tracée dans la variable `sample_id`

    all_coords, all_spectra, all_tic, all_sample_ids = [], [], [], []
    sample_offsets = {}   # {sample_name: (x_offset, y_offset)} pour éviter collisions spatiales

    x_offset_global = 0
    for file_idx, fpath in enumerate(IMZML_FILES):
        sname = os.path.splitext(os.path.basename(fpath))[0]
        parser = ImzMLParser(str(fpath))

        coords_f, tic_f = [], []
        # Pré-allouer par batch pour éviter les appends Python coûteux
        spectra_list = []

        for idx, (x, y, z) in enumerate(parser.coordinates):
            mzs, intensities = parser.getspectrum(idx)
            spec = np.zeros(N_BINS, dtype=np.float32)   # float32 : moitié moins de RAM
            for mz, intensity in zip(mzs, intensities):
                if MZ_MIN <= mz < MZ_MAX:
                    b = int((mz - MZ_MIN) / MZ_BIN_SIZE)
                    spec[min(b, N_BINS - 1)] += intensity
            coords_f.append([x + x_offset_global, y])
            tic_f.append(spec.sum())
            spectra_list.append(spec)

        coords_f  = np.array(coords_f, dtype=np.int32)
        spectra_f = np.array(spectra_list, dtype=np.float32);  del spectra_list
        tic_f     = np.array(tic_f, dtype=np.float32)

        sample_offsets[sname] = x_offset_global
        x_offset_global += int(coords_f[:, 0].max()) + 2   # gap de 2 px entre échantillons

        all_coords.append(coords_f)
        all_spectra.append(spectra_f)
        all_tic.append(tic_f)
        all_sample_ids.append(np.full(len(coords_f), file_idx, dtype=np.int8))

        print(f'{len(coords_f)} px  |  Median TIC={np.median(tic_f):.0f}')
        gc.collect()

    coords    = np.concatenate(all_coords,    axis=0)
    spectra   = np.concatenate(all_spectra,   axis=0)
    tic_all   = np.concatenate(all_tic,       axis=0)
    sample_id = np.concatenate(all_sample_ids,axis=0)
    del all_coords, all_spectra, all_tic, all_sample_ids;  gc.collect()

    n_pixels  = len(coords)
    x_max     = int(coords[:, 0].max()) + 1
    y_max     = int(coords[:, 1].max()) + 1
    n_samples = len(IMZML_FILES)


    print(f'✅ Total: {n_pixels} pixels  |  grid {x_max}×{y_max}  |  {n_samples} sample(s)')
    print(f'TIC — min={tic_all.min():.0f}  max={tic_all.max():.0f}  median={np.median(tic_all):.0f}  RAM spectra: {spectra.nbytes/1e6:.0f} MB')



# ══════════════════════════════════════════════════════════════════════════════
# TIC MAP / MASQUE TISSU
# ══════════════════════════════════════════════════════════════════════════════

def run_tic_map():
    '''lancement de la tic map'''

    # declaration global de variable qui serviront plus tard
    global spectra,spectra_filt,tissue_mask_1d,n_tissue,mz_filt,ion_keep

    # ── TIC normalisation ────────────────────────────────────────────────────────
    if NORMALIZE_TIC:
        tic_safe = np.where(tic_all > 0, tic_all, 1.0).astype(np.float32)
        spectra  = (spectra / tic_safe[:, np.newaxis]).astype(np.float32)
        print('✅ TIC-normalized ')

    # ── Filtrage ions rares ───────────────────────────────────────────────────────
    prevalence   = (spectra > ION_MIN_INTENSITY).mean(axis=0)
    ion_keep  = prevalence >= ION_MIN_PREVALENCE
    spectra_filt = np.ascontiguousarray(spectra[:, ion_keep], dtype=np.float32)
    mz_filt      = MZ_AXIS[ion_keep]
    del spectra;  import gc; gc.collect()
    print(f'✅ Retained ions: {ion_keep.sum()} / {N_BINS}  (prevalence ≥ {ION_MIN_PREVALENCE*100:.0f}%)')

    # ── Masque tissu (vectorisé) ──────────────────────────────────────────────────
    tic_thresh     = np.quantile(tic_all, TIC_TISSUE_QUANTILE) if AUTO_TISSUE_MASK else 0.0
    tissue_mask_1d = tic_all > tic_thresh

    mask_2d = np.zeros((y_max, x_max), dtype=bool)
    mask_2d[coords[:, 1].astype(int), coords[:, 0].astype(int)] = tissue_mask_1d
    mask_2d = binary_fill_holes(mask_2d)
    tissue_mask_1d = mask_2d[coords[:, 1].astype(int), coords[:, 0].astype(int)]

    n_tissue = tissue_mask_1d.sum()
    print(f'✅ Tissue mask: {n_tissue} px of fabric ({n_tissue/n_pixels*100:.1f}%)  |  {(~tissue_mask_1d).sum()} background')

    # ── Carte TIC + Masque + (si multi-samples) carte des échantillons ────────────
    n_panels = 3 if n_samples > 1 else 2
    fig, axs = plt.subplots(1, n_panels, figsize=(6 * n_panels, 5))
    fig.patch.set_facecolor("#ffffff")

    tic_map  = np.zeros((y_max, x_max), dtype=np.float32)
    mask_map = np.zeros((y_max, x_max), dtype=np.float32)
    tic_map[ coords[:, 1].astype(int), coords[:, 0].astype(int)] = tic_all
    mask_map[coords[:, 1].astype(int), coords[:, 0].astype(int)] = tissue_mask_1d.astype(float)

    for ax in axs: ax.set_facecolor("#0f0f1a")
    im0 = axs[0].imshow(tic_map,  cmap='inferno', origin='upper')
    axs[0].set_title('TIC Map', color='black'); axs[0].axis('off')
    plt.colorbar(im0, ax=axs[0]).ax.yaxis.set_tick_params(color='black')
    im1 = axs[1].imshow(mask_map, cmap='Greens',  origin='upper', vmin=0, vmax=1)
    axs[1].set_title(f'Tissue mask (q{TIC_TISSUE_QUANTILE*100:.0f})', color='black')
    axs[1].axis('off')
    plt.colorbar(im1, ax=axs[1]).ax.yaxis.set_tick_params(color='black')

    if n_samples > 1:
        sid_map = np.full((y_max, x_max), np.nan)
        sid_map[coords[:, 1].astype(int), coords[:, 0].astype(int)] = sample_id
        cmap_s = plt.colormaps['tab10'].resampled(n_samples)
        im2 = axs[2].imshow(sid_map, cmap=cmap_s, origin='upper',
                            vmin=-0.5, vmax=n_samples - 0.5, interpolation='nearest')
        axs[2].set_title('Sample', color='black'); axs[2].axis('off')
        cb2 = plt.colorbar(im2, ax=axs[2], ticks=range(n_samples))
        cb2.set_ticklabels([os.path.splitext(os.path.basename(f))[0] for f in IMZML_FILES])
        cb2.ax.yaxis.set_tick_params(color='black')
        plt.setp(cb2.ax.yaxis.get_ticklabels(), color='black', fontsize=7)

    plt.tight_layout()
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# PCA
# ══════════════════════════════════════════════════════════════════════════════

def run_PCA():
    '''lancement PCA + plot variance PCA'''

    # declaration global de variable qui serviront plus tard
    global spec_pca,tissue_idx,coords_tissue,spectra_tissue

    spectra_tissue = np.ascontiguousarray(spectra_filt[tissue_mask_1d], dtype=np.float32)
    coords_tissue  = coords[tissue_mask_1d]
    tissue_idx     = np.where(tissue_mask_1d)[0]

    # Remplacer dans la section PCA (cell 5)

    scaler   = StandardScaler()
    spec_sc  = scaler.fit_transform(spectra_tissue).astype(np.float32)
    # spec_sc  = scaler.fit_transform(spectra_tissue)          

    # IncrementalPCA si dataset volumineux (> 50k pixels) → économise la RAM
    if n_tissue > 50_000:
        print(f'  ℹ️  Large dataset ({n_tissue} px) → IncrementalPCA by batch')
        batch = min(5000, n_tissue // 10)
        pca   = IncrementalPCA(n_components=N_PCA_COMPONENTS)
        for start in range(0, n_tissue, batch):
            pca.partial_fit(spec_sc[start:start+batch])
        spec_pca = pca.transform(spec_sc).astype(np.float32)
    else:
        pca      = PCA(n_components=N_PCA_COMPONENTS, random_state=RANDOM_STATE)
        spec_pca = pca.fit_transform(spec_sc).astype(np.float32)

    cumvar = pca.explained_variance_ratio_.cumsum() * 100
    print(f'✅ PCA: {cumvar[-1]:.1f}% explained variance — {spec_sc.shape[1]} ions — {n_tissue} tissue pixels')

    fig, ax = plt.subplots(figsize=(8, 3))
    fig.patch.set_facecolor('#0f0f1a'); ax.set_facecolor('#111122')
    ax.bar(range(1, N_PCA_COMPONENTS + 1), pca.explained_variance_ratio_ * 100,
        color='#4cc9f0', alpha=0.85)
    ax.plot(range(1, N_PCA_COMPONENTS + 1), cumvar, 'o-', color='#f72585',
            markersize=5, lw=2, label='Cumulée')
    ax.set_xlabel('PCA Component', color='white')
    ax.set_ylabel('Variance (%)', color='white')
    ax.set_title('Explained variance — PCA (tissue only)', color='white')
    ax.tick_params(colors='white')
    for sp in ax.spines.values(): sp.set_color('#333')
    leg = ax.legend(fontsize=9)
    for t in leg.get_texts(): t.set_color('white')
    leg.get_frame().set_facecolor('#1a1a2e')
    plt.tight_layout()
    return fig

# ══════════════════════════════════════════════════════════════════════════════
# BISSECTION KMEAN ARBRE
# ══════════════════════════════════════════════════════════════════════════════

def run_bissceting_kmeans_tree():
    '''lancement Bissection Kmeans'''

    # declaration global de variable qui serviront plus tard
    global nodes,leaf_remap,labels_tissue
    def compute_sse(data, indices):
        sub = data[indices]
        return float(((sub - sub.mean(axis=0)) ** 2).sum())


    def local_silhouette(data, idx_L, idx_R, sample_size=3000, rs=42):
        """Silhouette calculé LOCALEMENT sur les 2 enfants uniquement."""
        combined = np.concatenate([idx_L, idx_R])
        lbl      = np.array([0]*len(idx_L) + [1]*len(idx_R), dtype=int)
        sub      = data[combined]
        n = len(combined)
        if n < 4 or len(np.unique(lbl)) < 2:
            return -1.0
        if n > sample_size:
            rng = np.random.default_rng(rs)
            sel = rng.choice(n, size=sample_size, replace=False)
            sub, lbl = sub[sel], lbl[sel]
        return float(silhouette_score(sub, lbl))


    def bisecting_kmeans_tree(data, max_clusters=MAX_CLUSTERS,
                            sil_threshold=SILHOUETTE_THRESHOLD,
                            min_size=MIN_CLUSTER_SIZE,
                            n_init=N_INIT_KMEANS, rs=RANDOM_STATE):
        """
        Bisecting K-Means corrigé :
        - Chaque bissection crée DEUX nouveaux nœuds avec des IDs distincts
        - global_labels est mis à jour pour les deux enfants à chaque étape
        - Le comptage de feuilles est exact → MAX_CLUSTERS respecté
        """
        n       = data.shape[0]
        next_id = 1   # nœud racine = 0

        nodes = {0: dict(node_id=0, parent_id=None, depth=0,
                        pixel_idx=np.arange(n),
                        sse=compute_sse(data, np.arange(n)),
                        sil_local=None, is_leaf=True)}
        global_labels = np.zeros(n, dtype=int)   # tous dans le nœud 0
        frozen        = set()
        tree_log      = []

        hdr = f'  {"Step":>4}  {"Node":>5}  {"Pixels":>7}  {"→[L,R]":>9}  {"SSE":>13}  {"Sil_loc":>8}  Decision'
        print('='*75)
        print(f'  BKM  max_clusters={max_clusters}  local_threshold={sil_threshold}')
        print('='*75); print(hdr); print('-'*75)

        step = 0
        while True:
            # Feuilles actives (non gelées, assez grandes)
            leaves_now = [nid for nid, nd in nodes.items() if nd['is_leaf']]
            if len(leaves_now) >= max_clusters:
                print(f'  ⏹  MAX_CLUSTERS={max_clusters} has been reached.'); break

            active = [nid for nid in leaves_now
                    if nid not in frozen
                    and len(nodes[nid]['pixel_idx']) >= min_size * 2]
            if not active:
                print(' ⏹  No more divisible clusters.'); break

            # Choisir la feuille à plus grande SSE
            tid   = max(active, key=lambda nid: nodes[nid]['sse'])
            t_idx = nodes[tid]['pixel_idx']

            km2 = KMeans(n_clusters=2, n_init=n_init, random_state=rs)
            sub_lbl = km2.fit_predict(data[t_idx])
            idx_L   = t_idx[sub_lbl == 0]
            idx_R   = t_idx[sub_lbl == 1]

            sil  = local_silhouette(data, idx_L, idx_R, rs=rs)
            step += 1
            dec  = '✅ accepted' if sil >= sil_threshold else '🔒 frozen'
            lid, rid = next_id, next_id + 1
            print(f'  {step:4d}  {tid:5d}  {len(t_idx):7d}  [{lid},{rid}]'
                f'  {nodes[tid]["sse"]:13.1f}  {sil:8.4f}  {dec}')

            if sil < sil_threshold:
                frozen.add(tid)
                continue

            # Créer deux nouveaux nœuds enfants avec IDs frais
            next_id += 2
            pd_depth = nodes[tid]['depth']

            # Marquer le nœud parent comme non-feuille
            nodes[tid]['is_leaf'] = False

            nodes[lid] = dict(node_id=lid, parent_id=tid, depth=pd_depth + 1,
                            pixel_idx=idx_L, sse=compute_sse(data, idx_L),
                            sil_local=sil, is_leaf=True)
            nodes[rid] = dict(node_id=rid, parent_id=tid, depth=pd_depth + 1,
                            pixel_idx=idx_R, sse=compute_sse(data, idx_R),
                            sil_local=sil, is_leaf=True)

            # Mettre à jour les labels globaux pour les deux enfants
            global_labels[idx_L] = lid
            global_labels[idx_R] = rid

            tree_log.append(dict(step=step, parent_id=tid,
                                left_id=lid, right_id=rid,
                                n_left=len(idx_L), n_right=len(idx_R),
                                sil_local=sil,
                                merge_height=nodes[lid]['sse'] + nodes[rid]['sse']))

        print('='*75)
        leaves     = sorted(nid for nid, nd in nodes.items() if nd['is_leaf'])
        leaf_remap = {old: new for new, old in enumerate(leaves)}
        final_lbl  = np.array([leaf_remap[global_labels[i]] for i in range(n)])
        n_cl       = len(leaves)
        print(f'  ✅ {n_cl} final clusters')
        return final_lbl, nodes, tree_log, n_cl, leaf_remap


    # ── Run ───────────────────────────────────────────────────────────────────────
    # declaration global de variable qui serviront plus tard
    global labels_all, n_clusters, bkm_nodes, tree_log,leaf_remap,unique_clusters
    labels_tissue, bkm_nodes, tree_log, n_clusters, leaf_remap = \
        bisecting_kmeans_tree(spec_pca)

    labels_all = np.full(n_pixels, -1, dtype=int)
    labels_all[tissue_idx] = labels_tissue
    unique_clusters = sorted(np.unique(labels_tissue))
    print(f'  Clusters : {unique_clusters}')

    if tree_log:
        xs = [h['step']      for h in tree_log]
        ys = [h['sil_local'] for h in tree_log]

        fig, ax = plt.subplots(figsize=(9, 4))
        ax.plot(xs, ys, 'o-', color='royalblue', lw=2, markersize=8)
        for x, y in zip(xs, ys):
            ax.annotate(f'{y:.3f}', (x, y), textcoords='offset points',
                        xytext=(0, 9), ha='center', fontsize=8)
        ax.axhline(SILHOUETTE_THRESHOLD, color='red', ls='--',
                label=f'Seuil = {SILHOUETTE_THRESHOLD}')
        ax.set_xlabel('Bissection Step'); ax.set_ylabel('Local Silhouette')
        ax.set_title('Local Silhouette Score at Each Bisection')
        ax.legend(); ax.grid(True, alpha=0.3)
        plt.tight_layout()

        df_log = pd.DataFrame(tree_log)[['step','parent_id','left_id','right_id',
                                        'n_left','n_right','sil_local']]
        df_log['sil_local'] = df_log['sil_local'].map('{:.4f}'.format)
        print("-----------------------------------------------------------------------------------")
        print(df_log.to_string(index=False))

        return fig

# ══════════════════════════════════════════════════════════════════════════════
# DENDROGRAMME
# ══════════════════════════════════════════════════════════════════════════════

def run_dendrogramme():
    '''lancement dendrogramme'''
    # declaration global de variable qui serviront plus tard
    global coords_tissue,labels_tissue
    def draw_dendro(nodes, tree_log, leaf_remap, n_tissue):
        if not tree_log:
            print('No bisection.'); return

        children_of  = {}
        split_height = {}
        for h in tree_log:
            p, l, r = h['parent_id'], h['left_id'], h['right_id']
            children_of[p]  = [l, r]
            split_height[p] = h['merge_height']

        leaves   = sorted(nid for nid, nd in nodes.items() if nd['is_leaf'])
        n_leaves = len(leaves)
        cmap_d   = plt.colormaps['tab20c'].resampled(max(n_leaves, 2))
        leaf_x   = {lid: i for i, lid in enumerate(leaves)}

        def sub_leaves(start):
            result, stack, visited = [], [start], set()
            while stack:
                nid = stack.pop()
                if nid in visited: continue
                visited.add(nid)
                if nid in children_of:
                    stack.extend(children_of[nid])
                else:
                    result.append(nid)
            return result

        node_x, node_y = {}, {}
        for nid in nodes:
            sl = [leaf_x[l] for l in sub_leaves(nid) if l in leaf_x]
            if sl: node_x[nid] = np.mean(sl)
            node_y[nid] = split_height.get(nid, 0.0)

        max_h = max(node_y.values(), default=1)
        fig, ax = plt.subplots(figsize=(max(14, n_leaves * 2.2), 8))
        fig.patch.set_facecolor('#0f0f1a')
        ax.set_facecolor('#0f0f1a')

        for p, (l, r) in children_of.items():
            px, py = node_x.get(p, 0), node_y.get(p, 0)
            lx, ly = node_x.get(l, 0), node_y.get(l, 0)
            rx, ry = node_x.get(r, 0), node_y.get(r, 0)
            ax.plot([lx, rx], [py, py], color='#8ecae6', lw=1.8, alpha=0.8)
            ax.plot([lx, lx], [ly, py], color='#8ecae6', lw=1.8, alpha=0.8)
            ax.plot([rx, rx], [ry, py], color='#8ecae6', lw=1.8, alpha=0.8)
            h_e = next((h for h in tree_log if h['parent_id'] == p), None)
            if h_e:
                ax.text(px, py + max_h * 0.025,
                        f"Sil={h_e['sil_local']:.3f}",
                        ha='center', fontsize=7.5, color='#ffd166', fontweight='bold')

        for rank, lid in enumerate(leaves):
            new_id = leaf_remap.get(lid, rank)
            color  = cmap_d(new_id / max(n_leaves - 1, 1))
            n_px   = len(nodes[lid]['pixel_idx'])
            pct    = n_px / n_tissue * 100
            bar_h  = node_y.get(lid, 0) + max_h * 0.04
            ax.bar(leaf_x[lid], height=bar_h, width=0.72, bottom=0,
                color=color, alpha=0.9, zorder=3,
                edgecolor='white', linewidth=0.4)
            ax.text(leaf_x[lid], -max_h * 0.07,
                    f'C{new_id}\n{n_px}px\n{pct:.1f}%',
                    ha='center', va='top', fontsize=7.5, color='white')

        ax.set_xticks([])
        ax.set_ylabel('SSE (parent inertia before bisection)', fontsize=10, color='white')
        ax.set_title('Dendrogram — Bisecting K-Means MALDI-MSI\n'
                    '(height = parent SSE, annotated local silhouette, color = final cluster)',
                    fontsize=10, color='white', pad=12,y=0.98)
        ax.tick_params(colors='white')
        for spine in ax.spines.values(): spine.set_visible(False)
        plt.tight_layout()
        return fig

    return draw_dendro(bkm_nodes, tree_log, leaf_remap, n_tissue)

# ══════════════════════════════════════════════════════════════════════════════
# CARTES SPATIALES
# ══════════════════════════════════════════════════════════════════════════════

def run_cartes_spatiales():
    "lancement Cartes spatiales"
    # declaration global de variable qui serviront plus tard
    global cmap_main

    def make_msi_cmap(n):
        """Combine tab10 + Set2 + Set3 pour maximiser la distinction visuelle."""
        base_colors = []
        for cmap_name in ['tab10', 'Set2', 'Set3', 'tab20b']:
            cm = plt.colormaps[cmap_name]
            base_colors += [cm(i / (cm.N - 1)) for i in range(cm.N)]
        # Déduplique et tronque
        seen, uniq = set(), []
        for c in base_colors:
            key = tuple(round(x, 3) for x in c)
            if key not in seen:
                seen.add(key); uniq.append(c)
        return ListedColormap(uniq[:max(n, 2)])

    cmap_main = make_msi_cmap(n_clusters)

    # ── Image finale ──────────────────────────────────────────────────────────────
    xs_t = coords_tissue[:, 0].astype(int)
    ys_t = coords_tissue[:, 1].astype(int)
    img_final = np.full((y_max, x_max), np.nan)
    img_final[ys_t, xs_t] = labels_tissue

    fig, ax = plt.subplots(figsize=(11, 9))
    fig.patch.set_facecolor('#0f0f1a')
    ax.set_facecolor('#0f0f1a')

    im = ax.imshow(img_final, cmap=cmap_main, origin='upper',
                vmin=-0.5, vmax=n_clusters - 0.5, interpolation='nearest')

    # Contour du masque tissu
    mask_img = np.zeros((y_max, x_max), dtype=float)
    mask_img[ys_t, xs_t] = 1.0
    ax.contour(mask_img, levels=[0.5], colors=['white'], linewidths=[0.6], alpha=0.5)

    ax.set_title(f'Bisecting K-Means — {n_clusters} clusters (tissue only)',
                fontsize=14, color='white', pad=12,y=0.98)
    ax.axis('off')

    # Légende compacte en grille
    n_cols_leg = 4 if n_clusters > 8 else 2
    patches = [mpatches.Patch(
                facecolor=cmap_main((c + 0.5) / n_clusters),
                edgecolor='white', linewidth=0.4,
                label=f'C{c}  {(labels_tissue==c).sum()} px  ' +
                        f'({(labels_tissue==c).sum()/n_tissue*100:.1f}%)')
            for c in unique_clusters]
    leg = ax.legend(handles=patches, loc='lower center',
                    bbox_to_anchor=(0.5, -0.02 - 0.045 * ((n_clusters - 1) // n_cols_leg)),
                    ncol=n_cols_leg, fontsize=7.5, framealpha=0.25,
                    labelcolor='white', edgecolor='#555')
    leg.get_frame().set_facecolor('#1a1a2e')

    plt.tight_layout()
    return fig

# ══════════════════════════════════════════════════════════════════════════════
# CARTES DE TOUTE LES ETAPES DE LA BISSECTION
# ══════════════════════════════════════════════════════════════════════════════

def run_all_cartes_spatiales():
    "Lancement de toute les cartes spatiales"

    # Rappel d'une ancienne sous fonction
    def make_msi_cmap(n):
        """Combine tab10 + Set2 + Set3 pour maximiser la distinction visuelle."""
        base_colors = []
        for cmap_name in ['tab10', 'Set2', 'Set3', 'tab20b']:
            cm = plt.colormaps[cmap_name]
            base_colors += [cm(i / (cm.N - 1)) for i in range(cm.N)]
        # Déduplique et tronque
        seen, uniq = set(), []
        for c in base_colors:
            key = tuple(round(x, 3) for x in c)
            if key not in seen:
                seen.add(key); uniq.append(c)
        return ListedColormap(uniq[:max(n, 2)])



    if tree_log:
        # ── Reconstruire la progression en utilisant leaf_remap ──────────────────
        # Clé du fix : on recrée chaque étape depuis l'état FINAL des labels
        # en remontant l'arbre depuis tree_log, ce qui respecte les noeuds gelés.

        n_steps   = len(tree_log)
        # k réel à chaque étape = nombre de feuilles actives après s bissections acceptées
        # (les nœuds gelés ne génèrent pas d'entrée dans tree_log)
        k_at_step = list(range(1, n_steps + 2))   # 1 → 2 → ... → n_steps+1

        ncols = min(5, n_steps + 1)
        nrows = ((n_steps + 1) + ncols - 1) // ncols
        fig, axs = plt.subplots(nrows, ncols,
                                figsize=(4.2 * ncols, 3.8 * nrows), squeeze=False)
        fig.patch.set_facecolor('#0f0f1a')

        # Reconstruire la progression étape par étape avec un compteur indépendant
        # leaf_remap ne connaît que les feuilles finales → inutilisable pour les
        # nœuds intermédiaires ; on utilise un compteur next_label croissant.
        step_maps = []
        cur_lbl = np.zeros(n_tissue, dtype=np.int32)   # étape 0 : k=1
        step_maps.append(cur_lbl.copy())

        next_label = 1   # nouveau label attribué à chaque bissection (fils droit)
        for h in tree_log:
            new_lbl  = cur_lbl.copy()
            left_px  = bkm_nodes[h['left_id']]['pixel_idx']
            right_px = bkm_nodes[h['right_id']]['pixel_idx']
            # Le fils gauche hérite du label courant du parent (déjà dans cur_lbl)
            # Le fils droit reçoit un nouveau label unique pour cette étape
            new_lbl[right_px] = next_label
            next_label += 1
            step_maps.append(new_lbl.copy())
            cur_lbl = new_lbl

        xs_t = coords_tissue[:, 0].astype(int)
        ys_t = coords_tissue[:, 1].astype(int)
        cmap_prog = make_msi_cmap(n_clusters + 2)

        for s, sl in enumerate(step_maps):
            row, col = divmod(s, ncols)
            ax = axs[row][col]
            ax.set_facecolor('#0f0f1a')
            n_c = len(np.unique(sl))
            img = np.full((y_max, x_max), np.nan)
            img[ys_t, xs_t] = sl
            ax.imshow(img, cmap=cmap_prog, origin='upper',
                    vmin=-0.5, vmax=n_clusters - 0.5,
                    interpolation='nearest')
            title = f'k={n_c}' if s > 0 else 'k=1'
            if s > 0: title += f'  Sil={tree_log[s-1]["sil_local"]:.3f}'
            ax.set_title(title, fontsize=8, color='white')
            ax.axis('off')

        for s in range(len(step_maps), nrows * ncols):
            row, col = divmod(s, ncols)
            axs[row][col].set_visible(False)

        plt.suptitle('Segmentation Progress — Only accepted bisections',
                    fontsize=12, y=0.98, color='white')
        plt.tight_layout()
        return fig


# ══════════════════════════════════════════════════════════════════════════════
# UMAP
# ══════════════════════════════════════════════════════════════════════════════

def run_UMAP():
    "Lancement de l'UMAP"
    # declaration global de variable qui serviront plus tard
    global embedding
    reducer   = umap.UMAP(n_neighbors=UMAP_N_NEIGHBORS, min_dist=UMAP_MIN_DIST,
                        n_components=UMAP_N_COMPONENTS, random_state=RANDOM_STATE)
    embedding = reducer.fit_transform(spec_pca)

    fig, ax = plt.subplots(figsize=(9, 7))
    sc = ax.scatter(embedding[:,0], embedding[:,1], c=labels_tissue,
                    cmap='tab20', s=4, alpha=0.7, vmin=-0.5, vmax=n_clusters-0.5)
    plt.colorbar(sc, ax=ax, ticks=range(n_clusters)).set_label('Cluster')
    ax.set_title('UMAP — all tissue clusters')
    ax.set_xlabel('UMAP 1'); ax.set_ylabel('UMAP 2')
    plt.tight_layout()
    return fig

# ══════════════════════════════════════════════════════════════════════════════
# UMAP CHAQUE CLUSTER
# ══════════════════════════════════════════════════════════════════════════════

def run_all_UMAP():
    "Lancement de l'UMAP de tout les cluster individuel"
    ncols = min(4, n_clusters)
    nrows = (n_clusters + ncols - 1) // ncols
    fig, axs = plt.subplots(nrows, ncols, figsize=(5*ncols, 4*nrows), squeeze=False)
    fig.patch.set_facecolor('#0f0f1a')

    # Recalcul local si sil_samples pas encore dispo
    _sil = silhouette_samples(spec_pca, labels_tissue)

    for idx, cid in enumerate(unique_clusters):
        row, col = divmod(idx, ncols)
        ax    = axs[row][col]
        ax.set_facecolor('#111122')
        mask  = labels_tissue == cid
        color = cmap_main(cid / max(n_clusters - 1, 1))
        ax.scatter(embedding[~mask,0], embedding[~mask,1], c='#222', s=2, alpha=0.3)
        ax.scatter(embedding[mask,0],  embedding[mask,1],  color=color, s=7, alpha=0.9)
        ax.set_title(f'C{cid}  |  {mask.sum()} px  |  Sil={_sil[mask].mean():.3f}',
                    fontsize=8, color='white')
        ax.set_xlabel('UMAP 1', fontsize=7, color='#aaa')
        ax.set_ylabel('UMAP 2', fontsize=7, color='#aaa')
        ax.tick_params(colors='#aaa', labelsize=6)
        for sp in ax.spines.values(): sp.set_color('#333')

    for idx in range(n_clusters, nrows*ncols):
        row, col = divmod(idx, ncols)
        axs[row][col].set_visible(False)
    plt.suptitle('UMAP per cluster', fontsize=13, y=0.995, color='white')
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    return fig


# ══════════════════════════════════════════════════════════════════════════════════
#DISTRIBUTION SPATIALE PAR ECHANTILLON / SILHOUETTE BAR CHART / VIOLIN PAR CLUSTER
# ══════════════════════════════════════════════════════════════════════════════════


def run_multi_echantillons_bar_chart_violin():
    "Lancement multi echantillongage / silhouette bar chart / violin par cluster"
    # Rappel d'une ancienne sous fonction
    def make_msi_cmap(n):
        """Combine tab10 + Set2 + Set3 pour maximiser la distinction visuelle."""
        base_colors = []
        for cmap_name in ['tab10', 'Set2', 'Set3', 'tab20b']:
            cm = plt.colormaps[cmap_name]
            base_colors += [cm(i / (cm.N - 1)) for i in range(cm.N)]
        # Déduplique et tronque
        seen, uniq = set(), []
        for c in base_colors:
            key = tuple(round(x, 3) for x in c)
            if key not in seen:
                seen.add(key); uniq.append(c)
        return ListedColormap(uniq[:max(n, 2)])

    # initialisation pour le cas mono-échantillon (fig1 / fig2 non créées)
    fig1, fig2 = None, None

    # ── Si multi-échantillons : carte cluster colorée par sample ─────────────────
    if n_samples > 1:
        fig1, axs = plt.subplots(1, n_samples, figsize=(9 * n_samples, 8), squeeze=False)
        fig1.patch.set_facecolor('#0f0f1a')
        xs_t = coords_tissue[:, 0].astype(int)
        ys_t = coords_tissue[:, 1].astype(int)
        sample_tissue = sample_id[tissue_mask_1d]

        for fi, fpath in enumerate(IMZML_FILES):
            sname = os.path.splitext(os.path.basename(fpath))[0]
            ax = axs[0][fi]
            ax.set_facecolor('#0f0f1a')
            img = np.full((y_max, x_max), np.nan)
            mask_s = sample_tissue == fi
            img[ys_t[mask_s], xs_t[mask_s]] = labels_tissue[mask_s]
            ax.imshow(img, cmap=make_msi_cmap(n_clusters), origin='upper',
                    vmin=-0.5, vmax=n_clusters - 0.5, interpolation='nearest')
            ax.set_title(sname, fontsize=11, color='white')
            ax.axis('off')
        plt.suptitle('Segmentation by Sample', fontsize=13, color='white', y=0.995)
        plt.tight_layout(rect=[0, 0, 1, 0.96])

        # Distribution des clusters par échantillon (bar chart empilé)
        fig2, ax = plt.subplots(figsize=(max(8, n_clusters * 0.7), 5))
        fig2.patch.set_facecolor('#0f0f1a'); ax.set_facecolor('#111122')
        x_pos = np.arange(n_clusters)
        bottoms = np.zeros(n_clusters)
        cmap_s = plt.colormaps['tab10'].resampled(n_samples)
        for fi, fpath in enumerate(IMZML_FILES):
            sname = os.path.splitext(os.path.basename(fpath))[0]
            mask_s = sample_tissue == fi
            counts = np.array([(labels_tissue[mask_s] == c).sum() for c in unique_clusters], dtype=float)
            totals = np.array([(labels_tissue == c).sum() for c in unique_clusters], dtype=float)
            pcts   = np.where(totals > 0, counts / totals * 100, 0)
            ax.bar(x_pos, pcts, bottom=bottoms, color=cmap_s(fi), alpha=0.85,
                label=sname, width=0.7, edgecolor='#222', linewidth=0.3)
            bottoms += pcts
        ax.set_xticks(x_pos); ax.set_xticklabels([f'C{c}' for c in unique_clusters], color='white')
        ax.set_ylabel('% of pixels in the cluster', color='white')
        ax.set_title('Composition by sample within each cluster', color='white')
        ax.tick_params(colors='white')
        for sp in ax.spines.values(): sp.set_color('#333')
        leg = ax.legend(fontsize=9)
        for t in leg.get_texts(): t.set_color('white')
        leg.get_frame().set_facecolor('#1a1a2e')
        plt.tight_layout()
    else:
        print("  ℹ️  A single sample — multi-sample graphs not shown")

    sil_samples = silhouette_samples(spec_pca, labels_tissue)

    fig3, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig3.patch.set_facecolor('#0f0f1a')
    for ax in axes: ax.set_facecolor('#111122')

    # ── Bar chart silhouette moyen par cluster ────────────────────────────────────
    sil_means = [sil_samples[labels_tissue == c].mean() for c in unique_clusters]
    colors_bar = [cmap_main(c / max(n_clusters - 1, 1)) for c in unique_clusters]
    axes[0].barh(unique_clusters, sil_means, color=colors_bar, alpha=0.9,
                edgecolor='#333', height=0.7)
    axes[0].axvline(0, color='white', lw=1, alpha=0.5)
    axes[0].axvline(np.mean(sil_samples), color='#ffd166', lw=1.5, ls='--',
                    label=f'Moy. globale = {np.mean(sil_samples):.3f}')
    axes[0].set_yticks(unique_clusters)
    axes[0].set_yticklabels([f'C{c}' for c in unique_clusters], color='white')
    axes[0].set_xlabel('Average Silhouette Score', color='white')
    axes[0].set_title('Silhouette per cluster', color='white')
    axes[0].tick_params(colors='white')
    for sp in axes[0].spines.values(): sp.set_color('#333')
    leg = axes[0].legend(fontsize=8)
    for t in leg.get_texts(): t.set_color('white')
    leg.get_frame().set_facecolor('#1a1a2e')

    # ── Violin silhouette ─────────────────────────────────────────────────────────
    violin_data = [sil_samples[labels_tissue == c] for c in unique_clusters]
    vp = axes[1].violinplot(violin_data, positions=unique_clusters,
                            showmedians=True, showextrema=False)
    for i, (body, cid) in enumerate(zip(vp['bodies'], unique_clusters)):
        body.set_facecolor(cmap_main(cid / max(n_clusters - 1, 1)))
        body.set_alpha(0.75)
    vp['cmedians'].set_color('white'); vp['cmedians'].set_linewidth(2)
    axes[1].axhline(0, color='white', lw=0.8, alpha=0.4)
    axes[1].set_xticks(unique_clusters)
    axes[1].set_xticklabels([f'C{c}' for c in unique_clusters], color='white')
    axes[1].set_ylabel('Silhouette Score', color='white')
    axes[1].set_title('Silhouette Distribution by Cluster', color='white')
    axes[1].tick_params(colors='white')
    for sp in axes[1].spines.values(): sp.set_color('#333')

    plt.tight_layout()
    print(f'  Average overall silhouette: {np.mean(sil_samples):.4f}')
    return fig1, fig2, fig3


# ══════════════════════════════════════════════════════════════════════════════
# SPECTRES MOYENS PAR CLUSTER
# ══════════════════════════════════════════════════════════════════════════════

def run_spectre_moyen_cluster():
    "Lancement des spectre moyen par cluster"
    # ── Spectres moyens — CLUSTERS FINAUX UNIQUEMENT ────────────────────────────
    # unique_clusters contient les labels remappés 0..n_clusters-1 après BKM
    global_mean_spec = spectra_tissue.mean(axis=0)

    ncols = min(3, n_clusters)
    nrows = (n_clusters + ncols - 1) // ncols
    fig, axs = plt.subplots(nrows, ncols,
                            figsize=(8 * ncols, 3.8 * nrows), squeeze=False)
    fig.patch.set_facecolor('#0f0f1a')

    for idx, cid in enumerate(unique_clusters):
        row, col = divmod(idx, ncols)
        ax    = axs[row][col]
        ax.set_facecolor('#111122')
        mask  = labels_tissue == cid
        ms    = spectra_tissue[mask].mean(axis=0)
        ss    = spectra_tissue[mask].std(axis=0)
        color = cmap_main(cid / max(n_clusters - 1, 1))

        # Fond global en gris
        ax.fill_between(mz_filt, global_mean_spec, alpha=0.15, color='white', zorder=1)
        ax.plot(mz_filt, global_mean_spec, color='#888', lw=0.7, label='Global', zorder=2)

        # Spectre du cluster
        ax.fill_between(mz_filt, ms - ss, ms + ss, alpha=0.18, color=color, zorder=3)
        ax.plot(mz_filt, ms, color=color, lw=1.3, label=f'C{cid}', zorder=4)

        # Annoter les 3 pics les plus intenses au-dessus du global
        ratio = ms / (global_mean_spec + 1e-12)
        top3  = np.argsort(ratio)[::-1][:3]
        for pk in top3:
            ax.annotate(f'{mz_filt[pk]:.1f}',
                        xy=(mz_filt[pk], ms[pk]),
                        xytext=(0, 6), textcoords='offset points',
                        ha='center', fontsize=6, color='white', alpha=0.9)

        n_px = mask.sum()
        ax.set_title(f'C{cid} — {n_px} px ({n_px/n_tissue*100:.1f}%) ± σ',
                    fontsize=9, color='white')
        ax.set_xlabel('m/z (Da)', fontsize=7, color='#aaa')
        ax.set_ylabel('Int. norm.',  fontsize=7, color='#aaa')
        ax.set_xlim(MZ_MIN, MZ_MAX)
        ax.tick_params(colors='#aaa', labelsize=6)
        for sp in ax.spines.values(): sp.set_color('#333')
        leg = ax.legend(fontsize=7, framealpha=0.3)
        for t in leg.get_texts(): t.set_color('white')

    for idx in range(n_clusters, nrows * ncols):
        row, col = divmod(idx, ncols)
        axs[row][col].set_visible(False)

    plt.suptitle(f'Average spectra — {n_clusters} final clusters',
                fontsize=13, y=0.98, color='white')
    plt.tight_layout()
    return fig

# ══════════════════════════════════════════════════════════════════════════════
# TOP PICS M/Z DISCRIMINANTS + TEST KRUSKAL-WALLIS
# ══════════════════════════════════════════════════════════════════════════════

def run_to_pic_mz_test_kruskal_wallis():
    "Lancement pic m/z discriminant et test de kruskal-wallis"
    # declaration global de variable qui serviront plus tard
    global sig_mask,df_peaks
    N_TOP = 15
    groups   = [spectra_tissue[labels_tissue == c] for c in unique_clusters]
    kw_pvals = []
    for b in range(ion_keep.sum()):
        try:
            _, p = kruskal(*[g[:, b] for g in groups])
        except Exception:
            p = 1.0
        kw_pvals.append(p)
    kw_pvals = np.array(kw_pvals)
    sig_mask = kw_pvals < 0.01
    print(f'✅ {sig_mask.sum()} significant ions (p<0.01) / {ion_keep.sum()}')

    peaks_rows = []
    print(f'\nTop {N_TOP} discriminant peaks per cluster (m/z in Da)\n' + '-'*60)
    global_mean_spec = spectra_tissue.mean(axis=0)
    for cid in unique_clusters:
        mask  = labels_tissue == cid
        cl_mean = spectra_tissue[mask].mean(axis=0)
        ratio   = np.where(global_mean_spec > 0, cl_mean / (global_mean_spec + 1e-12), 0)
        ratio[~sig_mask] = 0
        top_idx = np.argsort(ratio)[::-1][:N_TOP]
        top_mzs = [round(mz_filt[i], 2) for i in top_idx]
        print(f'  C{cid:2d} : {top_mzs}')
        for i in top_idx:
            peaks_rows.append({'cluster': cid, 'mz': round(mz_filt[i], 2),
                            'fold_change': round(ratio[i], 3),
                            'kruskal_pval': round(kw_pvals[i], 6)})
    df_peaks = pd.DataFrame(peaks_rows)

    # ── Volcano plot : fold-change vs -log10(p-val) par cluster ──────────────────
    ncols_v = min(4, n_clusters)
    nrows_v = (n_clusters + ncols_v - 1) // ncols_v
    fig, axs = plt.subplots(nrows_v, ncols_v,
                            figsize=(5 * ncols_v, 4 * nrows_v), squeeze=False)
    fig.patch.set_facecolor('#0f0f1a')

    for idx, cid in enumerate(unique_clusters):
        row, col = divmod(idx, ncols_v)
        ax = axs[row][col];  ax.set_facecolor('#111122')
        mask    = labels_tissue == cid
        cl_mean = spectra_tissue[mask].mean(axis=0)
        fc      = np.log2((cl_mean + 1e-12) / (global_mean_spec + 1e-12))
        neglogp = -np.log10(kw_pvals + 1e-12)
        color   = cmap_main(cid / max(n_clusters - 1, 1))

        # Tous les ions en gris
        ax.scatter(fc, neglogp, s=3, alpha=0.3, color='#555')
        # Ions significatifs et up-régulés en couleur
        up = sig_mask & (fc > 0.5)
        ax.scatter(fc[up], neglogp[up], s=8, alpha=0.85, color=color, zorder=3)
        # Lignes de seuil
        ax.axhline(-np.log10(0.01), color='#ffd166', lw=0.8, ls='--', alpha=0.7)
        ax.axvline(0.5,  color='white', lw=0.6, ls=':', alpha=0.5)
        ax.axvline(-0.5, color='white', lw=0.6, ls=':', alpha=0.5)
        # Annoter top 3
        top3up = np.where(up)[0][np.argsort(fc[up])[::-1][:3]] if up.sum() >= 3 else np.where(up)[0]
        for pk in top3up:
            ax.annotate(f'{mz_filt[pk]:.1f}', xy=(fc[pk], neglogp[pk]),
                        xytext=(3, 3), textcoords='offset points',
                        fontsize=6, color='white', alpha=0.9)
        ax.set_title(f'Volcano C{cid}', fontsize=8, color='white')
        ax.set_xlabel('log2 FC', fontsize=7, color='#aaa')
        ax.set_ylabel('-log10 p', fontsize=7, color='#aaa')
        ax.tick_params(colors='#aaa', labelsize=6)
        for sp in ax.spines.values(): sp.set_color('#333')

    for idx in range(n_clusters, nrows_v * ncols_v):
        row, col = divmod(idx, ncols_v)
        axs[row][col].set_visible(False)
    plt.suptitle('Volcano plots — differentially expressed ions by cluster',
                fontsize=12, y=0.98, color='white')
    plt.tight_layout()
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# HEATMAP LIPIDIQUE INTER CLUSTERS
# ══════════════════════════════════════════════════════════════════════════════

def run_heatmap():
    "Lancement de la heatmap"
    # declaration global de variable qui serviront plus tard
    global top_hm_idx
    N_HM = 40
    cluster_means = np.vstack([spectra_tissue[labels_tissue==c].mean(axis=0)
                                for c in unique_clusters])
    inter_var     = cluster_means.std(axis=0)
    inter_var_sig = inter_var.copy(); inter_var_sig[~sig_mask] = 0
    top_hm_idx    = np.argsort(inter_var_sig)[::-1][:N_HM]
    top_mzs_hm    = np.round(mz_filt[top_hm_idx], 2)

    hm_data   = cluster_means[:, top_hm_idx]
    hm_data_z = (hm_data - hm_data.mean(axis=0)) / (hm_data.std(axis=0) + 1e-12)

    fig, ax = plt.subplots(figsize=(max(14, N_HM*0.42), n_clusters*0.85 + 2))
    im = ax.imshow(hm_data_z, aspect='auto', cmap='RdBu_r', vmin=-2.5, vmax=2.5)
    ax.set_xticks(range(N_HM))
    ax.set_xticklabels([f'{m:.1f}' for m in top_mzs_hm], rotation=90, fontsize=7)
    ax.set_yticks(range(n_clusters))
    ax.set_yticklabels([f'Cluster {c}' for c in unique_clusters], fontsize=9)
    ax.set_xlabel('m/z (Da)', fontsize=10)
    ax.set_title(f'Lipid heatmap — Top {N_HM} discriminant ions (z-score, KW p<0.01)',
                fontsize=11)
    plt.colorbar(im, ax=ax, label='z-score')
    plt.tight_layout()
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# CARTES SPATIALES DES IONS LES PLUS DISCRIMINANTS
# ══════════════════════════════════════════════════════════════════════════════


def run_cartes_ions_discriminants():
    "Lancement de la carte des ions discriminant"
    N_ION_MAPS = 10
    ion_map_idx = top_hm_idx[:N_ION_MAPS]
    ncols_im = 5
    nrows_im = (N_ION_MAPS + ncols_im - 1) // ncols_im
    fig, axs = plt.subplots(nrows_im, ncols_im,
                            figsize=(5.5 * ncols_im, 5.0 * nrows_im), squeeze=False)
    fig.patch.set_facecolor('#0f0f1a')

    xs_t = coords_tissue[:, 0].astype(int)
    ys_t = coords_tissue[:, 1].astype(int)

    for rank, b_filt in enumerate(ion_map_idx):
        row, col = divmod(rank, ncols_im)
        ax = axs[row][col]
        ax.set_facecolor('black')
        mz_val = round(mz_filt[b_filt], 2)

        ion_map = np.full((y_max, x_max), np.nan)
        ion_map[ys_t, xs_t] = spectra_tissue[:, b_filt]

        # Normalisation par percentile pour mieux voir la dynamique
        vals = spectra_tissue[:, b_filt]
        vmin_p, vmax_p = np.percentile(vals, 2), np.percentile(vals, 98)

        im = ax.imshow(ion_map, cmap='inferno', origin='upper',
                    vmin=vmin_p, vmax=vmax_p, interpolation='nearest')
        ax.set_title(f'm/z = {mz_val} Da', fontsize=10, color='white', pad=4)
        ax.axis('off')
        cb = plt.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
        cb.set_label('Int. norm.', fontsize=7, color='white')
        cb.ax.yaxis.set_tick_params(color='white')
        plt.setp(cb.ax.yaxis.get_ticklabels(), color='white', fontsize=6)

    for rank in range(N_ION_MAPS, nrows_im * ncols_im):
        row, col = divmod(rank, ncols_im)
        axs[row][col].set_visible(False)

    plt.suptitle(f'Top {N_ION_MAPS} discriminant ions spatial maps (KW p<0.01)',
                fontsize=13, color='white', y=0.98)
    plt.tight_layout()
    return fig

# ══════════════════════════════════════════════════════════════════════════════
# EXPORT CSV
# ══════════════════════════════════════════════════════════════════════════════

chemin_export_csv = ""

def run_csv_export():
    "Lancement des exports CSV"

    # chemin_export_csv est defini lorsque l'utilisateur choisit un dossier via l'interface graphique
    # on utilise un dossier par defaut si la variable est vide
    chemin_dossier = chemin_export_csv if chemin_export_csv else "./CSV"
    # ── CSV pixels ────────────────────────────────────────────────────────────────
    df_pix = pd.DataFrame({
        'pixel_idx': tissue_idx,
        'x': coords_tissue[:,0].astype(int),
        'y': coords_tissue[:,1].astype(int),
        'sample_id': sample_id[tissue_mask_1d],
        'sample_name': [os.path.splitext(os.path.basename(IMZML_FILES[s]))[0]
                        for s in sample_id[tissue_mask_1d]],
        'cluster': labels_tissue,
        'tic': tic_all[tissue_idx],
        'umap_1': embedding[:,0],
        'umap_2': embedding[:,1],
    })
    for i in range(N_PCA_COMPONENTS):
        df_pix[f'pca_{i+1}'] = spec_pca[:,i]

    mz_cols = [f'mz_{mz:.2f}' for mz in mz_filt]
    df_spec = pd.DataFrame(spectra_tissue, columns=mz_cols)
    df_pix  = pd.concat([df_pix, df_spec], axis=1)
    chemin_fichier = os.path.join(chemin_dossier,CSV_PIXELS)
    df_pix.to_csv(chemin_fichier, index=False)
    print(f'✅ {CSV_PIXELS}  —  {df_pix.shape[0]} pixels × {df_pix.shape[1]} columns')

    # ── CSV spectres moyens ────────────────────────────────────────────────────────
    rows = []
    for cid in unique_clusters:
        mask = labels_tissue == cid
        ms   = spectra_tissue[mask].mean(axis=0)
        ss   = spectra_tissue[mask].std(axis=0)
        row  = {'cluster': cid, 'n_pixels': int(mask.sum())}
        for j, mz in enumerate(mz_filt):
            row[f'mean_mz_{mz:.2f}'] = round(float(ms[j]), 8)
            row[f'std_mz_{mz:.2f}']  = round(float(ss[j]), 8)
        rows.append(row)
    chemin_fichier = os.path.join(chemin_dossier,CSV_SPECTRA)
    pd.DataFrame(rows).to_csv(chemin_fichier, index=False)
    print(f'✅ {CSV_SPECTRA}  —  {n_clusters} clusters')

    # ── CSV pics discriminants ─────────────────────────────────────────────────────
    chemin_fichier = os.path.join(chemin_dossier,CSV_PEAKS)
    df_peaks.to_csv(chemin_fichier, index=False)
    print(f'✅ {CSV_PEAKS}  —  {len(df_peaks)} entries')

    df_pix[['pixel_idx','x','y','sample_name','cluster','tic','umap_1','umap_2']].head(5)


# ══════════════════════════════════════════════════════════════════════════════
# ANALYSE PKL — LABEL MAPS
# ══════════════════════════════════════════════════════════════════════════════

# Chemin vers le fichier pkl chargé par l'utilisateur (défini via l'interface)
chemin_pkl = ""
df_label_ratios = None

def run_label_maps():
    """Génère les label maps à partir du modèle pkl chargé, restreintes au masque tissu."""
    import joblib
    from scipy.ndimage import gaussian_filter, zoom as scipy_zoom

    imzml_file  = IMZML_FILES[0]
    model_file  = chemin_pkl
    mass_range  = (MZ_MIN, MZ_MAX)
    max_intensity_size = 4000
    sigma          = 0.5
    new_resolution = 3.0

    model       = joblib.load(model_file)
    p           = ImzMLParser(imzml_file)
    class_names = model.classes_

    mask_sample0 = (sample_id == 0) & tissue_mask_1d
    tissue_xy = {(int(x), int(y)) for x, y in coords[mask_sample0]}

    label_maps = {label: np.zeros((y_max, x_max), dtype=np.float32) for label in class_names}

    for idx, (x, y, z) in enumerate(p.coordinates):
        if (x, y) in tissue_xy:
            mzs, intensities = p.getspectrum(idx)
            m = (mzs >= mass_range[0]) & (mzs <= mass_range[1])
            intensities = intensities[m]

            if len(intensities) > 0:
                if len(intensities) > max_intensity_size:
                    padded = intensities[:max_intensity_size]
                else:
                    padded = np.pad(intensities, (0, max_intensity_size - len(intensities)))

                scores = model.predict_proba(padded.reshape(1, -1))[0]

                for label_idx, label in enumerate(class_names):
                    label_maps[label][y, x] = scores[label_idx]

    n_labels = len(class_names)
    ncols = min(4, n_labels)
    nrows = (n_labels + ncols - 1) // ncols
    fig, axs = plt.subplots(nrows, ncols, figsize=(5 * ncols, 4.5 * nrows), squeeze=False)
    fig.patch.set_facecolor('#0f0f1a')

    for label_idx, label in enumerate(class_names):
        row, col = divmod(label_idx, ncols)
        ax = axs[row][col]
        ax.set_facecolor('black')

        smoothed = gaussian_filter(label_maps[label], sigma=sigma)
        zoomed   = scipy_zoom(smoothed, new_resolution, order=3)

        im = ax.imshow(zoomed, cmap='jet', vmin=0, vmax=1)
        cb = plt.colorbar(im, ax=ax, fraction=0.035, pad=0.02)
        cb.ax.yaxis.set_tick_params(color='white')
        plt.setp(cb.ax.yaxis.get_ticklabels(), color='white', fontsize=7)
        ax.set_title(str(label), fontsize=10, color='white', pad=4)
        ax.axis('off')

    for label_idx in range(n_labels, nrows * ncols):
        row, col = divmod(label_idx, ncols)
        axs[row][col].set_visible(False)

    plt.suptitle('Label Maps — PKL Model Prediction (tissue only)', fontsize=13, color='white', y=0.98)
    plt.tight_layout()
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# ANALYSE PKL — LABEL RATIOS
# ══════════════════════════════════════════════════════════════════════════════

def run_label_ratios():
    """Calcule et affiche les ratios de labels à partir du modèle pkl chargé, restreints au masque tissu."""
    import joblib

    imzml_file  = IMZML_FILES[0]
    model_file  = chemin_pkl
    mass_range  = (MZ_MIN, MZ_MAX)
    max_intensity_size = 4000

    model       = joblib.load(model_file)
    p           = ImzMLParser(imzml_file)
    class_names = model.classes_

    mask_sample0 = (sample_id == 0) & tissue_mask_1d
    tissue_xy = {(int(x), int(y)) for x, y in coords[mask_sample0]}

    label_sums = {label: 0.0 for label in class_names}
    n_tissue_px = 0

    for idx, (x, y, z) in enumerate(p.coordinates):
        if (x, y) in tissue_xy:
            mzs, intensities = p.getspectrum(idx)
            m = (mzs >= mass_range[0]) & (mzs <= mass_range[1])
            intensities = intensities[m]

            if len(intensities) > 0:
                if len(intensities) > max_intensity_size:
                    padded = intensities[:max_intensity_size]
                else:
                    padded = np.pad(intensities, (0, max_intensity_size - len(intensities)))

                scores = model.predict_proba(padded.reshape(1, -1))[0]
                n_tissue_px += 1
                for label_idx, label in enumerate(class_names):
                    label_sums[label] += scores[label_idx]

    global df_label_ratios

    total = sum(label_sums.values())
    ratios = {label: label_sums[label] / total for label in class_names}
    df_ratios = pd.DataFrame.from_dict(ratios, orient='index', columns=['Ratio'])
    print(df_ratios.to_string())
    df_label_ratios = df_ratios

    labels_list = list(ratios.keys())
    values      = [ratios[l] for l in labels_list]
    cmap_r      = plt.colormaps['tab10']
    colors      = [cmap_r(i / max(len(labels_list) - 1, 1)) for i in range(len(labels_list))]

    fig, ax = plt.subplots(figsize=(max(6, len(labels_list) * 1.2), 5))
    fig.patch.set_facecolor('#0f0f1a')
    ax.set_facecolor('#111122')
    bars = ax.bar(labels_list, values, color=colors, alpha=0.9, edgecolor='#222', linewidth=0.5)
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.005,
                f'{val:.3f}', ha='center', va='bottom', fontsize=9, color='white')
    ax.set_xlabel('Label', fontsize=10, color='white')
    ax.set_ylabel('Ratio', fontsize=10, color='white')
    ax.set_ylim(0, max(values) * 1.15 if values else 1)
    ax.set_title('Label Ratios — PKL Model Prediction (tissue only)', fontsize=12, color='white')
    ax.tick_params(colors='white')
    for sp in ax.spines.values():
        sp.set_color('#333')
    plt.tight_layout()
    return fig, df_ratios

def run_csv_export_label_ratios():
    "Lancement de l'export CSV des ratios de labels"

    chemin_dossier = chemin_export_csv if chemin_export_csv else "./CSV"
    chemin_fichier = os.path.join(chemin_dossier, CSV_LABEL_RATIOS)
    df_label_ratios.to_csv(chemin_fichier)
    print(f'✅ {CSV_LABEL_RATIOS}  —  {len(df_label_ratios)} labels')