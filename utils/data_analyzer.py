import pandas as pd
import numpy as np

class DataAnalyzer:
    def detect_all_issues(self, df):
        """
        Returns a dictionary of detected issues:
          - missing: Count of missing values per column.
          - duplicates: Count of duplicate rows.
          - dtypes: Potential mis-typed columns (e.g., numeric values stored as text).
          - outliers: Count of outlier observations per numeric column (using the IQR method).
          - formatting: Columns with inconsistent formatting in string data.
        """
        return {
            'missing': self._detect_missing(df),
            'duplicates': self._detect_duplicates(df),
            'dtypes': self._detect_dtype_issues(df),
            'outliers': self._detect_outliers(df),
            'formatting': self._detect_format_issues(df)
        }

    def _detect_missing(self, df):
        # Count missing values in each column
        return {col: int(df[col].isna().sum()) for col in df.columns}

    def _detect_duplicates(self, df):
        # Count duplicate rows
         return {"total_duplicates": int(df.duplicated().sum())}

    def _detect_dtype_issues(self, df):
        issues = {}
        # For object columns, try converting to numeric and flag if more than 80% are numeric.
        for col in df.columns:
            if df[col].dtype == 'object':
                non_null = df[col].dropna()
                if non_null.empty:
                    continue
                converted = pd.to_numeric(non_null, errors='coerce')
                ratio = converted.notna().sum() / non_null.shape[0]
                if ratio > 0.8:
                    issues[col] = 'Potential numeric values stored as text'
        return issues

    def _detect_outliers(self, df):
        outliers = {}
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        # Use the IQR method to count outliers for each numeric column
        for col in numeric_cols:
            q1 = df[col].quantile(0.25)
            q3 = df[col].quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            count = int(((df[col] < lower_bound) | (df[col] > upper_bound)).sum())
            outliers[col] = count
        return outliers

    def _detect_format_issues(self, df):
        issues = {}
        # For object columns, flag if any non-null value, when standardized, differs from the original
        cat_cols = df.select_dtypes(include=['object']).columns
        for col in cat_cols:
            standardized = df[col].dropna().apply(lambda x: x.strip().lower())
            if not standardized.equals(df[col].dropna()):
                issues[col] = "Inconsistent formatting detected"
        return issues
