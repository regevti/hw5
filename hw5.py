import pathlib
import json
import numpy as np
import pandas as pd
import seaborn as sns
from typing import Tuple, Union
import matplotlib.pyplot as plt


class QuestionnaireAnalysis:
    """
    Reads and analyzes data generated by the questionnaire experiment.
    Should be able to accept strings and pathlib.Path objects.
    """

    def __init__(self, data_fname: Union[pathlib.Path, str]):
        self.data_fname = pathlib.Path(data_fname)
        if not self.data_fname.exists():
            raise ValueError(f'File {self.data_fname} does not exist')
        self.data = None

    def read_data(self):
        """Reads the json data located in self.data_fname into memory, to
        the attribute self.data.
        """
        self.data = pd.read_json(self.data_fname)

    def show_age_distrib(self) -> Tuple[np.ndarray, np.ndarray]:
        """Calculates and plots the age distribution of the participants.
        Returns
        -------
        hist : np.ndarray
          Number of people in a given bin
        bins : np.ndarray
          Bin edges
        """
        counts, bins = np.histogram(self.data['age'].dropna(), bins=np.arange(0, 101, 10))
        plt.hist(counts, bins)
        plt.xlabel("Age [years]")
        plt.title("age distribution of the participants")
        plt.show()
        return counts, bins

    def remove_rows_without_mail(self) -> pd.DataFrame:
        """Checks self.data for rows with invalid emails, and removes them.

        Returns
        -------
        df : pd.DataFrame
          A corrected DataFrame, i.e. the same table but with the erroneous rows removed and
          the (ordinal) index after a reset.
            """
        return self.data['email'][self.data['email'].str.contains(r'\w+@\w.\w+')].reset_index()

    def fill_na_with_mean(self) -> Tuple[pd.DataFrame, np.ndarray]:
        """Finds, in the original DataFrame, the subjects that didn't answer
        all questions, and replaces that missing value with the mean of the
        other grades for that student.

        Returns
        -------
        df : pd.DataFrame
          The corrected DataFrame after insertion of the mean grade
        arr : np.ndarray
              Row indices of the students that their new grades were generated
            """
        q_columns = self.data.columns[self.data.columns.str.contains(r'q\d')]
        na_rows = self.data[self.data[q_columns].isna().any(axis=1)].index
        return self.data[q_columns].fillna(self.data[q_columns].mean()), na_rows

    def score_subjects(self, maximal_nans_per_sub: int = 1) -> pd.DataFrame:
        """Calculates the average score of a subject and adds a new "score" column
        with it.

        If the subject has more than "maximal_nans_per_sub" NaN in his grades, the
        score should be NA. Otherwise, the score is simply the mean of the other grades.
        The datatype of score is UInt8, and the floating point raw numbers should be
        rounded down.

        Parameters
        ----------
        maximal_nans_per_sub : int, optional
            Number of allowed NaNs per subject before giving a NA score.

        Returns
        -------
        pd.DataFrame
            A new DF with a new column - "score".
        """
        score_df = self.data.copy()
        q_columns = self.data.columns[self.data.columns.str.contains(r'q\d')]
        score = pd.Series(score_df[q_columns].mean(numeric_only=True, axis=1).apply(np.floor).astype('UInt8'))
        score[score_df[q_columns].isna().sum(axis=1) > maximal_nans_per_sub] = pd.NA
        score_df['score'] = score

        return score_df

    def correlate_gender_age(self) -> pd.DataFrame:
        """Looks for a correlation between the gender of the subject, their age
        and the score for all five questions.

        Returns
        -------
        pd.DataFrame
            A DataFrame with a MultiIndex containing the gender and whether the subject is above
            40 years of age, and the average score in each of the five questions.
        """
        corr_df = self.data.copy()
        q_columns = self.data.columns[self.data.columns.str.contains(r'q\d')]
        corr_df['age'] = corr_df['age'] > 40
        corr_df.index = pd.MultiIndex.from_tuples(zip(corr_df.index,corr_df['gender'],corr_df['age']))
        corr_df = corr_df[q_columns].groupby(level=[1, 2]).mean()
        corr_df.plot.bar()
        plt.show()
        return corr_df