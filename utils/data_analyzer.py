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
          - class_imbalance: Class imbalance check for categorical-like numeric columns.
          - lexical_issues: Columns with potential lexical mistakes.
          - categorical_conversion_needed: Categorical columns that may need conversion.
        """
        return {
            'missing': self._detect_missing(df),
            'duplicates': self._detect_duplicates(df),
            'dtypes': self._detect_dtype_issues(df),
            'outliers': self._detect_outliers(df),
            'formatting': self._detect_format_issues(df),
            'class_imbalance': self._check_class_imbalance(df),
            'lexical_issues': self._detect_lexical_issues(df),
            'categorical_conversion_needed': self._detect_categorical_conversion(df)
        }

    def _detect_missing(self, df):
        return {col: int(df[col].isna().sum()) for col in df.columns}

    def _detect_duplicates(self, df):
        return {"total_duplicates": int(df.duplicated().sum())}

    def _detect_dtype_issues(self, df):
        issues = {}
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
        cat_cols = df.select_dtypes(include=['object']).columns
        for col in cat_cols:
            standardized = df[col].dropna().apply(lambda x: x.strip().lower())
            if not standardized.equals(df[col].dropna()):
                issues[col] = "Inconsistent formatting detected"
        return issues

    def _check_class_imbalance(self, df):
        imbalance = {}
        for col in df.columns:
            if df[col].nunique() <= 10:
                if pd.api.types.is_numeric_dtype(df[col]) or pd.api.types.is_categorical_dtype(df[col]) or df[col].dtype == 'object':
                    imbalance[col] = df[col].value_counts(normalize=True).to_dict()
        return imbalance

    def _detect_lexical_issues(self, df):
        lexical_issues = {}
        text_cols = df.select_dtypes(include=['object']).columns
        for col in text_cols:
            unique_values = df[col].dropna().unique()
            for val in unique_values:
                if len(val.split()) == 1 and not val.isalpha():
                    lexical_issues[col] = "Potential lexical issues detected"
                    break
        return lexical_issues

    def _detect_categorical_conversion(self, df):
        categorical_conversion = {}
        cat_cols = [col for col in df.select_dtypes(include=['object']).columns if df[col].nunique() <= 10]
        for col in cat_cols:
            categorical_conversion[col] = "May need label encoding"
        return categorical_conversion
