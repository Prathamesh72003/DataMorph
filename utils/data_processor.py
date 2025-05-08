import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
from spellchecker import SpellChecker
from sklearn.impute import KNNImputer
from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import IterativeImputer
from scipy.stats import skew, zscore
import re
from sklearn.preprocessing import OrdinalEncoder, LabelEncoder
from sklearn.feature_extraction import FeatureHasher
import jieba
import nltk
from textblob import TextBlob
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

nltk.download('punkt')
nltk.download('stopwords')

class DataProcessor:
    def __init__(self):
        self.applied_methods = {}
        self.strategies = {}
        self.missing_strategies={}
        self.outlier_strategies={}
        self.encoding_strategies={}
        self.integrity_strategies={}

    def select_strategies(self, df, target_column=None):
        """Detect and store all strategies for various issues."""
        self.missing_strategies = self.detect_missing_value_strategy(df)
        print("1")
        self.integrity_strategies = self.detect_data_integrity_strategy(df)
        print("2")
        self.outlier_strategies = self.detect_outliers(df)
        print("3")
        self.encoding_strategies = self.detect_categorical_encoding_strategy(df, target_column)
        print("4")

    def process_data(self, df, selected_issues=None):
        self.select_strategies(df)

        print("5")
        if selected_issues is None:
            selected_issues = ['duplicates', 'dtypes', 'missing', 'outliers', 'formats', 'spelling', 'class_imbalance']
        
        print("6")
        if 'duplicates' in selected_issues:
            df = self._handle_duplicates(df)
        
        print("7")
        if 'dtypes' in selected_issues:
            df = self._resolve_data_integrity_strategy(df)
        
        print("8")
        if 'missing' in selected_issues:
            df = self._handle_missing(df)
        
        print("9")
        if 'outliers' in selected_issues:
            df = self._handle_outliers(df)
        
        print("10")
        if 'formats' in selected_issues:
            df = self._standardize_formats(df)


        print("11")
        if 'spelling' in selected_issues:
            df = self._correct_spelling(df)
            # df = self._resolve_lexical_issues_df(df)

        print("12")
        df = self._resolve_lexical_issues_df(df)

        print("13")
        df = self._apply_categorical_encoding(df)

        print("14")
        return df
        
    def detect_missing_value_strategy(self, df):
        strategies = {}
        numeric_cols = df.select_dtypes(include=['number']).columns
        
        for column in df.columns:
            if df[column].isna().sum() == 0:
                continue

            # dtype = df[column].dtype
            is_numerical = column in numeric_cols
            # print(dtype)
            unique_values = df[column].nunique()
            strategy = "Mode (Discrete numerical data)"

            if is_numerical:  # Numerical data
                if unique_values <= 10:  
                    strategy = "Mode (Discrete numerical data)"
                else:
                    # Detect outliers using IQR
                    q1, q3 = np.nanpercentile(df[column].dropna(), [25, 75])
                    iqr = q3 - q1
                    lower_bound, upper_bound = q1 - 1.5 * iqr, q3 + 1.5 * iqr
                    has_outliers = ((df[column] < lower_bound) | (df[column] > upper_bound)).sum() > 0
                    strategy = "Median (Continuous numerical data with outliers)" if has_outliers else "Mean (Continuous numerical data without outliers)"
            else:  # Categorical data
                strategy = "Mode (Categorical data)"

            strategies[column] = strategy
            print(f"Column: {column}, Strategy: {strategy}")
        
        return strategies
    
    def detect_data_integrity_strategy(self, df):
        """
        Detects data integrity issues and suggests strategies for handling them.
        """
        strategies = {}

        for col in df.columns:
            col_dtype = df[col].dtype

            # Check for explicit type casting needs
            if col_dtype == 'object':
                if df[col].str.isnumeric().sum() / len(df[col]) > 0.8:
                    strategies[col] = "Explicit Type Casting (Convert to numeric)"
                elif df[col].nunique() / len(df[col]) < 0.1:
                    strategies[col] = "Explicit Type Casting (Convert to category)"
            
            # Check for implicit type coercion
            elif np.issubdtype(col_dtype, np.number):
                if df[col].isna().sum() > 0:
                    strategies[col] = "Implicit Type Coercion (Handle NaN with mean/median)"
            
            # Check for pattern-based format enforcement
            if "date" in col.lower() or "time" in col.lower():
                strategies[col] = "Pattern-based Format Enforcement (Convert to datetime)"
            elif "phone" in col.lower():
                strategies[col] = "Pattern-based Format Enforcement (Ensure numeric format)"
            elif "id" in col.lower():
                strategies[col] = "Pattern-based Format Enforcement (Ensure consistent length and format)"

        return strategies
    
    def detect_outliers(self,df):
        """Detects the best outlier handling strategy for each numeric column."""
        numeric_cols = df.select_dtypes(include=['number']).columns
        detected_strategies = {}

        for col in numeric_cols:
            data = df[col].dropna()

            detected_strategies[col] = "Winsorization (Capping Outliers)"

            if data.nunique() <= 10:
                detected_strategies[col] = "Winsorization (Capping Outliers)"
                continue  # Skip further checks

            skewness = data.skew()
            is_skewed = abs(skewness) > 1

            # Compute IQR-based outliers
            q1, q3 = np.percentile(data, [25, 75])
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            has_outliers = ((data < lower_bound) | (data > upper_bound)).sum() > 0

            # Normality check (Z-Score method applicable)
            is_normal = (not is_skewed) and (len(data) > 30)

            if is_normal:
                detected_strategies[col] = "Z-Score-Based Filtering (Standard Deviation Method)"
            elif has_outliers:
                detected_strategies[col] = "Winsorization (Capping Outliers)"
            else:
                detected_strategies[col] = "No Outlier Handling Required"

        return detected_strategies
    
    def detect_categorical_encoding_strategy(self,df, target_column=None, high_cardinality_threshold=15):
        strategies = {}

        for col in df.select_dtypes(include=['object', 'category']).columns:
            unique_values = df[col].nunique()
            total_values = len(df[col])
            category_ratio = unique_values / total_values

            if target_column and target_column in df.columns:
                correlation = df.groupby(col)[target_column].mean().var()  # Check if category impacts target

            if unique_values == 2:
                strategy = "Binary Encoding (Label Encoding)"
            elif unique_values <= high_cardinality_threshold:
                if df[col].dtype.name == "category":
                    strategy = "Pandas Categorical Dtype"
                else:
                    strategy = "One-Hot Encoding (OHE)"
            elif unique_values > high_cardinality_threshold:
                if category_ratio < 0.05:
                    strategy = "Frequency Encoding"
                elif target_column and correlation > 0.01:
                    strategy = "Target Encoding"
                else:
                    strategy = "Hash Encoding (Feature Hashing)"
            else:
                strategy = "Ordinal Encoding (if meaningful order exists)"

            strategies[col] = strategy

        return strategies

    # ************************* Handling *****************************

    def _handle_missing(self, df):
        self.applied_methods['Missing Data'] = "Applied different strategies for missing data handling."

        for col, strategy in self.missing_strategies.items():
            if strategy.startswith("Mean"):
                df[col] = df[col].fillna(df[col].mean())
            elif strategy.startswith("Median"):
                df[col] = df[col].fillna(df[col].median())
            elif "Mode" in strategy:
                df[col] = df[col].fillna(df[col].mode()[0])
            elif "Backward Fill" in strategy:
                df[col] = df[col].fillna(method='bfill')
            elif "KNN Imputation" in strategy:
                imputer = KNNImputer(n_neighbors=5)
                df[col] = imputer.fit_transform(df[[col]])
            elif "Multivariate Imputation" in strategy:
                imputer = IterativeImputer()
                df[col] = imputer.fit_transform(df[[col]])

        return df

    def _handle_duplicates(self, df, subset=None, keep="first", strategy="full"):
        """
        Handles duplicate rows in the dataset.
        
        Parameters:
        - df (pd.DataFrame): The input dataframe.
        - subset (list, optional): Columns to consider for deduplication. Default is None (all columns).
        - keep (str, optional): Determines which duplicate to keep ("first", "last", False for removing all).
        - strategy (str, optional): "full" for removing all duplicates, "conditional" for domain-specific deduplication.

        Returns:
        - pd.DataFrame: Deduplicated dataframe.
        """
        
        initial_duplicates = df.duplicated(subset=subset).sum()
        
        if strategy == "full":
            # Full deduplication - remove exact duplicates across all columns
            df = df.drop_duplicates()
            self.applied_methods['Duplicate Data'] = f"Fully removed {initial_duplicates} exact duplicate rows."

        elif strategy == "conditional":
            # Conditional deduplication based on subset of columns
            if subset:
                df = df.drop_duplicates(subset=subset, keep=keep)
                self.applied_methods['Duplicate Data'] = f"Conditionally removed duplicates based on columns: {subset}"
            else:
                self.applied_methods['Duplicate Data'] = "No subset provided, full deduplication applied."
                df = df.drop_duplicates()

        return df


    # def _fix_dtypes(self, df):
    #     self.applied_methods['Data Type Correction'] = "Converted object columns to numeric where possible."
    #     for col in df.columns:
    #         if df[col].dtype == 'object':
    #             converted = pd.to_numeric(df[col], errors='coerce')
    #             if converted.notnull().mean() > 0.8:
    #                 df[col] = converted
    #     return df
    

    def _resolve_data_integrity_strategy(self, df):
        """
        Handles data integrity issues based on detected strategies.
        """
        # strategies = self.integrity_strategies

        for col, strategy in self.integrity_strategies.items():
            if strategy.startswith("Explicit Type Casting"):
                df = self._apply_type_casting(df, col)

            elif strategy.startswith("Implicit Type Coercion"):
                df = self._apply_type_coercion(df, col)

            elif strategy.startswith("Pattern-based Format Enforcement"):
                df = self._apply_format_enforcement(df, col)

        return df

    def _apply_type_casting(self, df, col):
        """Handles explicit type casting issues."""
        try:
            if df[col].str.isnumeric().sum() / len(df[col]) > 0.8:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            elif df[col].nunique() / len(df[col]) < 0.1:
                df[col] = df[col].astype('category')
            self.applied_methods[col] = "Applied Explicit Type Casting"
        except Exception as e:
            print(f"Type Casting Failed for {col}: {e}")
        return df

    def _apply_type_coercion(self, df, col):
        """Handles implicit type coercion issues."""
        if df[col].isna().sum() > 0:
            if df[col].nunique() > 10:
                df[col] = df[col].fillna(df[col].median())
            else:
                df[col] = df[col].fillna(df[col].mode()[0])
            self.applied_methods[col] = "Applied Implicit Type Coercion (Handled NaN)"
        return df

    def _apply_format_enforcement(self, df, col):
        """Handles pattern-based format enforcement issues."""
        if "date" in col.lower() or "time" in col.lower():
            df[col] = pd.to_datetime(df[col], errors='coerce')

        elif "phone" in col.lower():
            df[col] = df[col].astype(str).apply(lambda x: re.sub(r'\D', '', x) if pd.notna(x) else x)

        elif "id" in col.lower():
            df[col] = df[col].astype(str).str.zfill(6)  # Ensuring fixed length

        self.applied_methods[col] = "Applied Pattern-based Format Enforcement"
        return df

    # def _handle_outliers(self, df):
    #     self.applied_methods['Outliers'] = "Capped extreme values using IQR method."
    #     numeric_cols = df.select_dtypes(include=['number']).columns
    #     for col in numeric_cols:
    #         q1 = df[col].quantile(0.25)
    #         q3 = df[col].quantile(0.75)
    #         iqr = q3 - q1
    #         lower_bound = q1 - 1.5 * iqr
    #         upper_bound = q3 + 1.5 * iqr
    #         df[col] = df[col].clip(lower=lower_bound, upper=upper_bound)
    #     return df

    def _handle_outliers(self,df):
        """Applies the detected outlier handling strategy for each column."""
        numeric_cols = df.select_dtypes(include=['number']).columns
        for col, strategy in self.outlier_strategies.items():
            if col in numeric_cols:
                print("91")
                if strategy.startswith("Winsorization"):
                    print("92")
                    df=self._winsorize(df,col)
                elif strategy == strategy.startswith("Z-Score-Based Filtering"):
                    print("93")
                    df=self._zscore_filter(df,col)
                # elif strategy == "IQR-Based Filtering (Interquartile Range Method)":
                #     print("94")
                #     df=self._iqr_filter(df,col)
        return df

    def _winsorize(self, df, col):
        """Capping extreme values for discrete data"""
        numeric_cols = df.select_dtypes(include=['number']).columns
        for col in numeric_cols:
            q1 = df[col].quantile(0.25)
            q3 = df[col].quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            df[col] = df[col].clip(lower=lower_bound, upper=upper_bound)
        return df

    def _zscore_filter(self, df, col, threshold=3):
        """Removes outliers using Z-Score method"""
        z_scores = np.abs(zscore(df[col]))
        df = df[z_scores < threshold]
        return df

    def _iqr_filter(self, col):
        """Removes outliers using IQR method"""
        q1, q3 = np.percentile(self.df[col], [25, 75])
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        df = df[(df[col] >= lower_bound) & (df[col] <= upper_bound)]

        return df
    
    # def _standardize_formats(self, df):
    #     self.applied_methods['Format Standardization'] = "Trimmed whitespace and converted text to lowercase."
    #     cat_cols = df.select_dtypes(include=['object']).columns
    #     for col in cat_cols:
    #         df[col] = df[col].str.strip().str.lower()
    #     return df
    
    def _standardize_formats(self,df):
        df = df.copy()
        issues = {}

        for col in df.columns:
            if df[col].dtype == "object":
                # Detect issues
                issues[col] = {
                    "case_inconsistencies": df[col].apply(lambda x: isinstance(x, str) and x != x.lower()).sum(),
                    "leading_trailing_spaces": df[col].apply(lambda x: isinstance(x, str) and (x.startswith(" ") or x.endswith(" "))).sum(),
                    "multiple_spaces": df[col].apply(lambda x: isinstance(x, str) and bool(re.search(r'\s{2,}', x))).sum(),
                    "non_numeric_phone": df[col].apply(lambda x: isinstance(x, str) and col.lower() == "phone" and not x.replace(" ", "").isdigit()).sum(),
                    "date_format_issues": df[col].apply(lambda x: isinstance(x, str) and col.lower() == "date" and not bool(re.match(r'\d{4}-\d{2}-\d{2}', x))).sum(),
                }

                # Resolve issues
                if col.lower() not in ["name"]:  # Preserve capitalization for names
                    df[col] = df[col].str.lower()

                df[col] = df[col].str.strip()  # Remove leading/trailing spaces
                df[col] = df[col].str.replace(r'\s+', ' ', regex=True)  # Normalize spaces

                # Standardize phone numbers (remove non-digits and format)
                if "phone" in col.lower():
                    df[col] = df[col].str.replace(r'\D', '', regex=True)
                    df[col] = df[col].apply(lambda x: f"({x[:3]}) {x[3:6]}-{x[6:]}" if len(x) == 10 else x)

                # Standardize dates to YYYY-MM-DD format
                if "date" in col.lower():
                    df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%Y-%m-%d')

        return df

    def _correct_spelling(self, df):
        self.applied_methods['Spelling Correction'] = "Fixed spelling issues using spellchecker library."
        spell = SpellChecker()
        cat_cols = df.select_dtypes(include=['object']).columns
        for col in cat_cols:
            df[col] = df[col].apply(lambda x: spell.correction(x) if isinstance(x, str) else x)
        return df
    
    def _lexical_normalization(self, text):
        """ Corrects spelling and expands common abbreviations. """
        if not isinstance(text, str):
            return text  # Skip non-string values

        corrected_text = str(TextBlob(text).correct())

        abbreviations = {
            "u": "you",
            "r": "are",
            "btw": "by the way",
            "gonna": "going to",
            "wanna": "want to",
            "teh": "the"
        }
        
        words = word_tokenize(corrected_text)
        expanded_words = [abbreviations[word] if word in abbreviations else word for word in words]
        
        return ' '.join(expanded_words)

    def _token_pruning(self, text):
        """ Removes stopwords from the text. """
        if not isinstance(text, str):
            return text

        stop_words = set(stopwords.words('english'))
        words = word_tokenize(text)
        filtered_words = [word for word in words if word.lower() not in stop_words]
        return ' '.join(filtered_words)

    def _lexical_segmentation(self, text):
        """ Splits hashtags, camelCase words, and segments Chinese/Japanese text. """
        if not isinstance(text, str):
            return text

        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)  # CamelCase splitting
        text = re.sub(r'#(\w+)', lambda m: ' '.join(re.findall('[A-Z][^A-Z]*', m.group(1))), text)  # Hashtags
        
        # Segment Chinese/Japanese text
        if re.search(r'[\u4e00-\u9fff]', text):
            text = " ".join(jieba.cut(text))
        
        return text

    def _resolve_lexical_issues_df(self, df, text_columns=None):
        """
        Applies lexical issue resolution to a DataFrame.
        
        Parameters:
            df (pd.DataFrame): The input DataFrame.
            text_columns (list, optional): List of text column names. If None, detects automatically.

        Returns:
            pd.DataFrame: Processed DataFrame with cleaned text.
        """
        if text_columns is None:
            # Auto-detect text columns
            text_columns = df.select_dtypes(include=['object']).columns.tolist()

        df_cleaned = df.copy()
        
        for col in text_columns:
            print(f"Processing column: {col}")

            df_cleaned[col] = df_cleaned[col].astype(str)  # Ensure column is string
            df_cleaned[col] = df_cleaned[col].apply(self.lexical_normalization)
            df_cleaned[col] = df_cleaned[col].apply(self.token_pruning)
            df_cleaned[col] = df_cleaned[col].apply(self.lexical_segmentation)

        return df_cleaned

    # def _handle_inconsistent_data_conversion(self, df):
    #     self.applied_methods['Categorical Conversion'] = "Applied Label Encoding to categorical columns with ≤10 unique values."
    #     le = LabelEncoder()
    #     for col in df.columns:
    #         if df[col].dtype == 'object' and df[col].nunique() <= 10:
    #             df[col] = le.fit_transform(df[col])
    #     return df
    
    def _apply_categorical_encoding(self,df, target_column=None, hash_features=10):
        df_encoded = df.copy()

        for col, strategy in self.encoding_strategies.items():
            if strategy == "Binary Encoding (Label Encoding)":
                encoder = LabelEncoder()
                df_encoded[col] = encoder.fit_transform(df_encoded[col])

            elif strategy == "One-Hot Encoding (OHE)":
                df_encoded = pd.get_dummies(df_encoded, columns=[col], drop_first=True)

            elif strategy == "Ordinal Encoding (if meaningful order exists)":
                encoder = OrdinalEncoder()
                df_encoded[col] = encoder.fit_transform(df_encoded[[col]])

            elif strategy == "Frequency Encoding":
                df_encoded[col] = df_encoded[col].map(df_encoded[col].value_counts())

            elif strategy == "Target Encoding" and target_column:
                target_mean = df_encoded.groupby(col)[target_column].mean()
                df_encoded[col] = df_encoded[col].map(target_mean)

            elif strategy.startswith("Hash Encoding"):
                hasher = FeatureHasher(n_features=hash_features, input_type='string')
                hashed_features = hasher.transform(df_encoded[col].astype(str))
                hashed_df = pd.DataFrame(hashed_features.toarray(), columns=[f"{col}_hash_{i}" for i in range(hash_features)])
                df_encoded = pd.concat([df_encoded.drop(columns=[col]), hashed_df], axis=1)

            elif strategy == "Pandas Categorical Dtype":
                df_encoded[col] = df_encoded[col].astype('category')

        return df_encoded