<p align="center">
  <img src="./logo.png" alt="imsCORE logo" width="250"/>
</p>



##  Table of Content

- [ Description](#-description)
- [ Installation](#-installation)
- [ A look at each analysis step by step](#-a-look-at-each-analysis-step-by-step)
- [ Usage](#-usage)
- [ Citation](#-citation)

##  Description

imsCORE is a standalone, cross-platform graphical application that packages a complete Mass Spectrometry Imaging (MSI) analysis pipeline — unsupervised segmentation and supervised classification — into a single, no-coding-required interface. It was built to make an analytical workflow originally developed as MATLAB scripts and expert-only notebooks accessible to any user, through a GUI built with PyQt5 and distributed as a standalone executable via PyInstaller.

The application takes one or several raw imzML files as input, bins each pixel spectrum onto a common m/z grid, applies TIC normalisation and removes rare, low-occupancy ions, and automatically derives a tissue mask from the resulting TIC image to restrict analysis to tissue-covered pixels. From there, two analysis modes are available:

- **Segmentation** — spectra are projected by PCA and segmented using a bisecting k-means scheme built on k-means++ initialisation, which recursively splits the most heterogeneous cluster and validates each split with a local silhouette score. This removes the need to fix the target number of clusters in advance: the algorithm refines the segmentation guided by an objective, data-driven stopping criterion. Results include spatial segmentation maps, a UMAP projection for cluster-separation assessment, per-cluster average spectra, and discriminant m/z features identified via the non-parametric Kruskal-Wallis test, rendered as volcano plots, heatmaps and spatial ion maps.
- **Classification** — a classification model trained elsewhere (for instance within [Profiler](https://prism-profiler.univ-lille.fr/)) is imported as a serialised `.pkl` file and applied pixel-by-pixel to the MSI dataset. Rather than a single hard label, the module computes a per-pixel probability for every class known to the model, rendered as spatially resolved probability maps, and summarises these into global class ratios averaged over all tissue pixels — a quantitative, per-sample estimate of tissue composition comparable across samples.

All pixel-level assignments, average spectra, class ratios and significant peaks are exported as CSV files for downstream statistical or biological interpretation, directly compatible with the Profiler ecosystem. An example CSV file can be found in the CSV folder of this repository.

##  Installation

- Download the ZIP file using the following link : [imsCORE Download](https://nextcloud.univ-lille.fr/index.php/s/DpKdcxjiFWAy9cj) 
- Once you have the ZIP file extract it
- Run the .exe file to launch the application


##  A look at each analysis step by step

There are currently two types of analysis:

- Segmentation using imzML file(s)
- Classification using a .pkl model file to analyze imzML data

The first two steps are common to both analyses:

1 - Raw MSI data is loaded using the pyimzML library and binned onto a fixed m/z grid.

2 - A TIC map is computed and used to automatically separate tissue pixels from background. Spectra are TIC-normalized, and low-prevalence ions are filtered out.

Once these are done, the rest of the analysis changes depending on the chosen analysis.

#### Segmentation

3 - Spectral dimensionality is reduced via Principal Component Analysis to speed up clustering.

4 - Tissue pixels are iteratively split into clusters using a bisecting K-Means strategy, with each split validated by a local silhouette score.The bisection tree is displayed to visualize the hierarchical structure of the segmentation.

5 - a dendrogramm of the local silhouette score is displayed

6 - Cluster assignments are projected onto the 2D tissue grid to produce segmentation maps at each bisection step.

7 - A 2D UMAP embedding is computed for visual exploration of cluster structure.

8 - Cluster quality is evaluated per cluster using silhouette scores.

9 - The Average spectra of each cluster is calculated

10 - A Kruskal-Wallis test identifies m/z values that significantly differ between clusters, visualized as volcano plots.

11 - The top discriminant ions are summarized in a z-score heatmap across clusters.

12 - The most discriminant ions are rendered as individual spatial intensity maps on the tissue.

13 - Results are exported as three CSV files: per-pixel data, per-cluster mean spectra, and a ranked list of discriminant peaks.

#### Classification

3 - Label maps are generated using the pkl file

4 - Label ratios are calculated using the pkl file 

##  Usage

To use this program, you need one imZML file (or two if you want to run multi-sample analysis). Additionally, you can choose to load a model file (.pkl) for different analyses (please refer to the [🔬 A look at each analysis step by step](#-a-look-at-each-analysis-step-by-step) section for further detail). Boot up the app (.exe) and select the imZML file using the GUI. Then, you can play with the settings before starting the analysis. I'm going to show you some examples of how this program works for each analysis using an imzML file of a rat brain.

#### Common to both analysis

Here is a quick look at the first menu: 

![ScreenShot](./README_screens/analysis_select.JPG)

You can choose what analysis you want to do simply by clicking on it's corresponding button. The next window that opens is differnet depending on which analysis you choosed : 

- If you choosed Segmentation here is what it looks like :

![ScreenShot](./README_screens/imzml_file_loading_segmentation.JPG)

- If you choosed Classification here is what it looks like :

![ScreenShot](./README_screens/imzml_file_loading_classification.JPG)

When you click on a button (execept the start analysis button of course) , the file explorer opens, allowing you to choose which imZML file you want to use for the analysis. There are currently no maximum to the amout of file you can select.

![ScreenShot](./README_screens/file_explorer.JPG)


Once you are done selecting your file(s) , you can click on the start analysis which will open the settings tab where the user can change the settings or use the default settings (this is step 1 of the [🔬 A look at each analysis step by step](#-a-look-at-each-analysis-step-by-step) section).

![ScreenShot](./README_screens/Settings.JPG)

Clicking on the default settings will automatically start the analysis, but if the user chooses to use custom settings, then another menu opens allowing the user to change the settings. Then the user needs to click on the save settings button to launch the analysis

This is what the custom settings menu looks like:

![ScreenShot](./README_screens/Custom_settings.JPG)

As you can see on this screen, there are multiple settings you can play with (and even more when you scroll) . If for any reason you don't know the purpose of a setting, just click on the ❓ for further detail

Once the analysis is started, a loading screen is displayed.

![ScreenShot](./README_screens/loading.JPG)

Every single step of the analysis has its own window in the GUI. Each window is built the same way :

- Graph, image or main info of the analysis (with a toolbar in order to allow the user to save Graphs/images shown on the window)
- sometimes other useful info is shown in the window
- a button to continue to the next part of the analysis

Here is what the second step looks like for both analysis :

![ScreenShot](./README_screens/step_2.JPG)

I am now going to walk you through each window corresponding to each step of  Segmentation . For more info about a step , please refer to the [🔬 A look at each analysis step by step](#-a-look-at-each-analysis-step-by-step) section:

#### Segmentation

##### step 3

![ScreenShot](./README_screens/step_3.JPG)

##### step 4

![ScreenShot](./README_screens/step_4.JPG)

##### step 5

![ScreenShot](./README_screens/step_5.JPG)

##### step 6

![ScreenShot](./README_screens/step_6.1.JPG)
![ScreenShot](./README_screens/step_6.2.JPG)

##### step 7

![ScreenShot](./README_screens/step_7.1.JPG)
![ScreenShot](./README_screens/step_7.2.JPG)

##### step 8

![ScreenShot](./README_screens/step_8.JPG)

##### step 9

![ScreenShot](./README_screens/step_9.JPG)

##### step 10

![ScreenShot](./README_screens/step_10.JPG)

##### step 11

![ScreenShot](./README_screens/step_11.JPG)

##### step 12

![ScreenShot](./README_screens/step_12.JPG)

##### step 13

At the end of the analysis , the CSV exports window allow the user to choose a folder to save the CSV exports. Here is what it looks like :

![ScreenShot](./README_screens/CSV_exports_segmentation.JPG)

Please note that the default folder for CSV exports is the CSV folder in this repository.

After this step, a final recap of the full analysis will be shown on the screen. This is what it looks like :

![ScreenShot](./README_screens/Final_recap_segmentation.JPG)

And that's it for Segmentation

I am now going to walk you through each window corresponding to each step of   Classification. For more info about a step, please refer to the [🔬 A look at each analysis step by step](#-a-look-at-each-analysis-step-by-step) section. Before that I just wanted to show you a small difference between Segmentation and Classification: the custom setting menu. Here is what it looks like when you are doing  Classification :

![ScreenShot](./README_screens/Custom_settings_pkl.JPG)

#### Classification

##### step 3

![ScreenShot](./README_screens/step_3_pkl.JPG)

##### step 4

![ScreenShot](./README_screens/step_4_pkl.JPG)

After this step is done you can export data as CSV using this menu that will show on screen after clicking the button on step 4 window :

![ScreenShot](./README_screens/CSV_exports_classification.JPG)

After the CSV export is done , like Segmentation , there is a final recap that will be shown on screen :

![ScreenShot](./README_screens/Final_recap_pkl.JPG)

##  Citation

If you use imsCORE in your research, please cite:

> Lagache L, Zirem Y, Le Rhun É, Fournier I, Salzet M. Predicting Protein Pathways Associated to Tumor Heterogeneity by Correlating Spatial Lipidomics and Proteomics: The Dry Proteomic Concept. *Mol Cell Proteomics*. 2025 Jan;24(1):100891. doi: [10.1016/j.mcpro.2024.100891](https://doi.org/10.1016/j.mcpro.2024.100891). Epub 2024 Dec 5. PMID: 39644924; PMCID: PMC11773152.

> Zirem Y, Ledoux L, Salzet M, Fournier I. Protocol to analyze 1D and 2D mass spectrometry data from glioblastoma tissues for cancer diagnosis and immune cell identification. *STAR Protoc*. 2024 Sep 20;5(3):103285. doi: [10.1016/j.xpro.2024.103285](https://doi.org/10.1016/j.xpro.2024.103285). Epub 2024 Sep 4. PMID: 39235938; PMCID: PMC11408140.
