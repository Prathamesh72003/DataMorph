import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import missingno as msno

class DataVisualization:
    def __init__(self):
        sns.set_theme(style="whitegrid")

    def visualize_all(self, df):
        """
        Generates key visualizations including:
          - Outlier detection: Box plot, violin plot, scatter plot
          - Missing values: Heatmap, bar chart, dendrogram
          - General data distribution: Histogram, KDE plot, pair plot, correlation heatmap
        """

        numeric_cols = df.select_dtypes(include=[np.number]).columns
        saved_files = []

        if len(numeric_cols) > 0:
            saved_files.append(self._plot_boxplot(df, numeric_cols[1]))
            saved_files.append(self._plot_violinplot(df, numeric_cols[0]))
            saved_files.append(self._plot_histogram(df, numeric_cols[0]))
            saved_files.append(self._plot_kdeplot(df, numeric_cols[0]))

        if len(numeric_cols) > 1:
            saved_files.append(self._plot_scatterplot(df, numeric_cols[0], numeric_cols[1]))

        saved_files.append(self._plot_missing_heatmap(df))
        saved_files.append(self._plot_missing_bar(df))
        saved_files.append(self._plot_missing_dendrogram(df))
        saved_files.append(self._plot_correlation_heatmap(df))

        if len(numeric_cols) > 2:
            saved_files.append(self._plot_pairplot(df, numeric_cols[:3]))
        
        return saved_files  

    def _save_plot(self, filename):
        filepath = f"static/visuals/{filename}"
        plt.savefig(filepath)
        plt.close()
        return filepath
    
    def _plot_boxplot(self, df, column):
        print(column)
        plt.figure(figsize=(6, 4))
        sns.boxplot(x=df[str(column)])
        plt.title(f"Box Plot of {column}")
        return self._save_plot(f"boxplot_{column}.png")

    def _plot_violinplot(self, df, column):
        plt.figure(figsize=(6, 4))
        sns.violinplot(x=df[column])
        plt.title(f"Violin Plot of {column}")
        return self._save_plot(f"violinplot_{column}.png")

    def _plot_scatterplot(self, df, x_col, y_col):
        plt.figure(figsize=(6, 4))
        sns.scatterplot(x=df[x_col], y=df[y_col])
        plt.title(f"Scatter Plot of {x_col} vs {y_col}")
        plt.xlabel(x_col)
        plt.ylabel(y_col)
        return self._save_plot(f"scatter_{x_col}_vs_{y_col}.png")

    def _plot_histogram(self, df, column):
        plt.figure(figsize=(6, 4))
        sns.histplot(df[column], bins=30, kde=True)
        plt.title(f"Histogram & KDE of {column}")
        return self._save_plot(f"histogram_{column}.png")

    def _plot_missing_heatmap(self, df):
        plt.figure(figsize=(6, 4))
        sns.heatmap(df.isnull(), cbar=False, cmap='viridis')
        plt.title("Missing Values Heatmap")
        return self._save_plot("missing_heatmap.png")

    def _plot_missing_bar(self, df):
        plt.figure(figsize=(6, 4))
        df.isnull().sum().plot(kind="bar", color='coral')
        plt.title("Missing Values Count")
        plt.ylabel("Count")
        return self._save_plot("missing_bar.png")

    def _plot_missing_dendrogram(self, df):
        plt.figure(figsize=(6, 4))
        msno.dendrogram(df)
        plt.title("Missing Values Dendrogram")
        return self._save_plot("missing_dendrogram.png")

    def _plot_pairplot(self, df, columns):
        sns.pairplot(df[columns])
        return self._save_plot("pairplot.png")

    def _plot_kdeplot(self, df, column):
        plt.figure(figsize=(6, 4))
        sns.kdeplot(df[column], fill=True, color='blue')
        plt.title(f"KDE Plot of {column}")
        return self._save_plot(f"kde_{column}.png")

    def _plot_correlation_heatmap(self, df):
        plt.figure(figsize=(6, 4))
        sns.heatmap(df.corr(numeric_only=True), annot=True, cmap='coolwarm', fmt=".2f", linewidths=0.5)
        plt.title("Correlation Heatmap")
        return self._save_plot("correlation_heatmap.png")
