def calculate_bkt(p_known: float, is_correct: bool) -> float:
    p_guess = 0.15
    p_slip = 0.10
    p_learn = 0.15

    prior = p_known
    if is_correct:
        posterior = (prior * (1 - p_slip)) / (prior * (1 - p_slip) + (1 - prior) * p_guess)
    else:
        posterior = (prior * p_slip) / (prior * p_slip + (1 - prior) * (1 - p_guess))

    return posterior + (1 - posterior) * p_learn