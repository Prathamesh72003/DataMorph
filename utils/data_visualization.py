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
        Generates visualizations:
        - Boxplots only for columns with outliers
        - Scatter plot for most highly correlated column pair
        - Histogram for the top numeric column
        - Missing value heatmap
        - Correlation heatmap
        """
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        saved_files = []

        # Correlation matrix and top correlated pair
        corr_matrix = df[numeric_cols].corr(numeric_only=True).abs()
        np.fill_diagonal(corr_matrix.values, 0)  # Ignore self-correlations

        # Find most highly correlated pair
        max_corr = corr_matrix.unstack().idxmax()
        x_col, y_col = max_corr
        # if corr_matrix.loc[x_col, y_col] > 0.5:  # Only plot if strong correlation
        saved_files.append(self._plot_scatterplot(df, x_col, y_col))

        # Histograms for top 3 columns with highest variance
        if numeric_cols:
            col_variances = df[numeric_cols].var().sort_values(ascending=False)
            top_var_cols = col_variances.head(3).index
            for col in top_var_cols:
                saved_files.append(self._plot_histogram(df, col))

        # Boxplot for numeric columns with outliers
        for col in numeric_cols:
            if self._has_outliers(df[col]):
                saved_files.append(self._plot_boxplot(df, col))

        saved_files.append(self._plot_missing_heatmap(df))
        saved_files.append(self._plot_correlation_heatmap(df))

        return saved_files

    def _save_plot(self, filename):
        filepath = f"static/visuals/{filename}"
        plt.tight_layout()
        plt.savefig(filepath)
        plt.close()
        return filepath

    def _has_outliers(self, series):
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        return ((series < lower_bound) | (series > upper_bound)).any()

    def _plot_boxplot(self, df, column):
        plt.figure(figsize=(6, 4))
        sns.boxplot(x=df[column])
        plt.title(f"Box Plot of {column}")
        return self._save_plot(f"boxplot_{column}.png")

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

    def _plot_correlation_heatmap(self, df):
        plt.figure(figsize=(6, 4))
        corr = df.corr(numeric_only=True)
        sns.heatmap(corr, annot=True, cmap='coolwarm', fmt=".2f", linewidths=0.5)
        plt.title("Correlation Heatmap")
        return self._save_plot("correlation_heatmap.png")
