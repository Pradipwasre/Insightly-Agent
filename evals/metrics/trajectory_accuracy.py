"""Trajectory Accuracy: how close is the actual tool sequence to the ideal one?

Uses the longest common subsequence (order matters):
    LCS(actual, expected) / max(len(actual), len(expected))
Extra retries and missing steps both lower the score.
"""


def lcs(a, b):
    table = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            table[i + 1][j + 1] = table[i][j] + 1 if x == y else max(table[i][j + 1], table[i + 1][j])
    return table[-1][-1]


def case_score(r):
    actual, expected = r["tools_used"], r["expected_tools"]
    if not actual and not expected:
        return 1.0
    return lcs(actual, expected) / max(len(actual), len(expected))


def score(records):
    return sum(case_score(r) for r in records) / len(records)
