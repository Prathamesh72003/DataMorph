import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
from spellchecker import SpellChecker

class DataProcessor:
    def __init__(self):
        self.applied_methods = {}

    def process_data(self, df, selected_issues=None):
        """
        Process the DataFrame by fixing issues.
        selected_issues: list of issues to process; valid options are:
           'duplicates', 'dtypes', 'missing', 'outliers', 'formats', 'spelling'
        If None, all issues will be processed.
        """
        if selected_issues is None:
            selected_issues = ['duplicates', 'dtypes', 'missing', 'outliers', 'formats', 'spelling', 'class_imbalance']
        
        if 'duplicates' in selected_issues:
            df = self._handle_duplicates(df)
        
        if 'dtypes' in selected_issues:
            df = self._fix_dtypes(df)
        
        if 'missing' in selected_issues:
            df = self._handle_missing(df)
        
        if 'outliers' in selected_issues:
            df = self._handle_outliers(df)
        
        if 'formats' in selected_issues:
            df = self._standardize_formats(df)

        if 'spelling' in selected_issues:
            df = self._correct_spelling(df)

        df = self._handle_inconsistent_data_conversion(df)

        # Display applied methods and first 10 rows
        # self._show_results(df)
        # self._download_cleaned_data(df)

        return df

    def _handle_missing(self, df):
        """Fill missing values: numerical columns with median; categorical columns with mode (or 'unknown' if no mode found)."""
        self.applied_methods['Missing Data'] = "Filled numerical columns with median and categorical columns with mode/unknown."
        
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())
        
        cat_cols = df.select_dtypes(include=['object']).columns
        for col in cat_cols:
            mode_val = df[col].mode()
            if not mode_val.empty:
                df[col] = df[col].fillna(mode_val[0])
            else:
                df[col] = df[col].fillna('unknown')
        
        return df

    def _handle_duplicates(self, df):
        """Remove duplicate rows."""
        self.applied_methods['Duplicate Data'] = f"Removed {df.duplicated().sum()} duplicate rows."
        return df.drop_duplicates()

    def _fix_dtypes(self, df):
        """Attempt to correct data types by converting object columns to numeric if possible."""
        self.applied_methods['Data Type Correction'] = "Converted object columns to numeric where at least 80% of values could be converted."
        
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                continue
            if df[col].dtype == 'object':
                converted = pd.to_numeric(df[col], errors='coerce')
                if converted.notnull().mean() > 0.8:
                    df[col] = converted
        return df

    def _handle_outliers(self, df):
        """Cap extreme values using the IQR method for all numeric columns."""
        self.applied_methods['Outliers'] = "Capped extreme values using IQR method."
        
        numeric_cols = df.select_dtypes(include=['number']).columns
        for col in numeric_cols:
            q1 = df[col].quantile(0.25)
            q3 = df[col].quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            df[col] = df[col].clip(lower=lower_bound, upper=upper_bound)
        return df

    def _standardize_formats(self, df):
        """Strip and convert all string columns to lowercase."""
        self.applied_methods['Format Standardization'] = "Trimmed whitespace and converted text to lowercase."
        
        cat_cols = df.select_dtypes(include=['object']).columns
        for col in cat_cols:
            df[col] = df[col].str.strip().str.lower()
        return df

    def _correct_spelling(self, df):
        """Correct spelling mistakes in text-based columns."""
        self.applied_methods['Spelling Correction'] = "Fixed spelling issues using spellchecker library."
        
        spell = SpellChecker()
        cat_cols = df.select_dtypes(include=['object']).columns
        for col in cat_cols:
            df[col] = df[col].apply(lambda x: spell.correction(x) if isinstance(x, str) else x)
        return df

    def _handle_inconsistent_data_conversion(self, df):
        """Convert categorical values into numeric values using Label Encoding for low-cardinality features."""
        self.applied_methods['Categorical Conversion'] = "Applied Label Encoding to categorical columns with ≤10 unique values."
        
        le = LabelEncoder()
        for col in df.columns:
            if df[col].dtype == 'object' and df[col].nunique() <= 10:
                df[col] = le.fit_transform(df[col])
        return df

