import pandas as pd
import numpy as np

class DataProcessor:
    def process_data(self, df, selected_issues=None):
        """
        Process the DataFrame by fixing issues.
        selected_issues: list of issues to process; valid options are:
           'duplicates', 'dtypes', 'missing', 'outliers', 'formats'
        If None, all issues will be processed.
        """
        if selected_issues is None:
            selected_issues = ['duplicates', 'dtypes', 'missing', 'outliers', 'formats']
        
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
        
        return df

    def _handle_missing(self, df):
        """Fill missing values: numerical columns with median; 
        categorical columns with mode (or 'unknown' if no mode found)."""
        # Process numeric columns
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())
        
        # Process categorical (object) columns
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
        return df.drop_duplicates()

    def _fix_dtypes(self, df):
        """Attempt to correct data types:
           - For object columns, convert to numeric if at least 80% of non-null values can be converted.
        """
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
        cat_cols = df.select_dtypes(include=['object']).columns
        for col in cat_cols:
            df[col] = df[col].str.strip().str.lower()
        return df
