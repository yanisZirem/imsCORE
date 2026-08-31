# imsCORE

[![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)](https://www.python.org/) ![Platform](https://img.shields.io/badge/Platform-Windows-green.svg) [![PyQt5](https://img.shields.io/badge/PyQt5-darkorange)](https://pypi.org/project/PyQt5/) [![Pyinstaller](https://img.shields.io/badge/Pyinstaller-purple)](https://pyinstaller.org/en/stable/index.html) [![PyImzml](https://img.shields.io/badge/PyImzml-darkblue)](https://pyimzml.readthedocs.io/en/latest/index.html)

## 📚 Table of Content

- [💬 Description](#-description)
- [📲 Installation](#-installation)
- [🔬 A look at each analysis step by step](#-a-look-at-each-analysis-step-by-step)
- [🚀 Usage](#-usage)

## 💬 Description

This project is a graphical user interface for the pipeline provided to me (imsCORE_pipeline.py), which I developed during my time as a trainee. The interface was built using the Python PyQt5 package and then converted into an executable file using PyInstaller. It allows users to analyze data from imzML mass spectrometry files. The analysis is divided into multiple steps, each represented by a dedicated window in the GUI. Once the analysis is complete, results are exported as CSV files. An example CSV file can be found in the CSV folder of this repository.

## 📲 Installation

- Download the ZIP file using the following link : [imsCORE Download](https://www.mediafire.com/file/nf15nkbhdzaf73a/imsCORE.zip/file) 
- Once you have the ZIP file extract it
- Run the .exe file to launch the application


## 🔬 A look at each analysis step by step

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

## 🚀 Usage

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