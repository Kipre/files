import numpy as np
import pandas as pd
from itertools import combinations_with_replacement

def open_csv(f):
	data = pd.read_csv(f)
	print(data)

def make_targets(df, derivative=False):
	'''
	Returns the X and X2 matrices for system identification.

		Parameters:
			df (pandas.DataFrame): The dataframe with variables
			derivative (bool): Whether we want X2 to be numerically differenciated.

		Returns:
			X, X2 (pandas.DataFrame, pandas.DataFrame): Tuple with the two resulting dataframes.
	'''
	# pass error on
	if 'error' in df.index:
		return df, df

	# sanity check
	if len(df.index) < 2: 
		error = pd.DataFrame(['The input csv must have more than 1 row'], index=['error'])
		return error, error

	# making X
	X = df.iloc[:-1].reset_index(drop=True)
	x_nans = X.isna().any(axis=1)

	# making X2
	if derivative:
		X2 = df.diff().iloc[1:].reset_index(drop=True)
	else:
		X2 = df.iloc[1:].reset_index(drop=True)
	x2_nans = X2.isna().any(axis=1)

	# removing NaNs
	X = X.loc[~(x_nans | x2_nans)]
	X2 = X2.loc[~(x_nans | x2_nans)]
	return X, X2

def augment(X, max_degree):
	'''
	Returns the augmented X matrix with polynomial terms.

		Parameters:
			X (pandas.DataFrame): The dataframe with variables.
			max_degree (int): Maximum degree of polynomial terms. 

		Returns:
			result (pandas.DataFrame): DataFrame with augmented states.
	'''
	# pass error on
	if 'error' in X.index:
		return X

	local_X = X.copy()
	local_X.insert(loc=0, column='1', value=1) # add constant

	variables = local_X.columns # fetch variables
	result = pd.DataFrame()

	for terms in combinations_with_replacement(variables, max_degree):
		result['*'.join(terms)] = local_X.loc[:, terms].prod(axis=1, numeric_only=True)

	return result

def sparse_regression(augmented, targets, cutoff=1e-4):
    """Implementation of the sparse regression algorithm as described 
    in https://arxiv.org/pdf/1509.03580.pdf

        Paramaters:
            augmented (pd.DataFrame): dataframe of shape (m, n) containing the states 
                augmented with the candidate functions.
            targets (pd.DataFrame): array of shape (m, k) containing the time 
                derivatives or the states at the next timestep.
            cutoff (float): 

        Returns:
            result (pd.DataFrame): The matrix of shape (n, k) of weights that minimize the problem.
    """
    # pass error on
    if 'error' in augmented.index:
        return augmented
    elif 'error' in targets.index:
        return targets

    # fetch the nb of variables and keep columns
    nb_variables = len(targets.columns)
    variables, terms = targets.columns, augmented.columns

    # solver
    solver = lambda A, B: np.linalg.lstsq(A, B, rcond=None)

    # make numpy arrays
    augmented = augmented.values
    targets = targets.values
    
    weights = solver(augmented, targets)[0]
    for iteration in range(5):
        precedent_weights = weights
        condition = np.abs(weights) > cutoff
        weights[~condition] = 0
        for i in range(nb_variables):
            big_indexes = condition[:, i]
            weights[big_indexes, i] = solver(augmented[:, big_indexes], targets[:, i])[0]
        if not (weights - precedent_weights).any():
            break # if no change from precedent interation, no need to continue
    return pd.DataFrame(weights, columns=variables, index=terms)

