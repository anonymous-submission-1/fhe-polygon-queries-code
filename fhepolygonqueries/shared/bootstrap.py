from openfhe import Ciphertext

from .sharedcontext import get_shared_context


# Perform bootstrapping only if there are not enough levels available
def bootstrap_if_needed(ciph: Ciphertext, needed_levels: int) -> Ciphertext:
    lvl = ciph.GetLevel()
    if lvl + needed_levels >= get_shared_context().mult_depth:
        print("Bootstrapping...")
        print("Before: ", ciph.GetLevel())
        ciph = get_shared_context().cc.EvalBootstrap(ciph, 2, 17)
        print("After: ", ciph.GetLevel())

    return ciph