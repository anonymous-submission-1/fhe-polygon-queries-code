from openfhe import *
#from .scale import scale_up_coords, scale_up_x, scale_up_y, scale_down_coords, scale_down_x, scale_down_y

import os
import psutil

from logging import debug as _debug, info as _info, getLogger, INFO

def get_memory_usage():
    """Returns the memory usage of the current Python process in MB."""
    process = psutil.Process(os.getpid())
    mem_bytes = process.memory_info().rss  # Resident Set Size: memory in RAM
    mem_mb = mem_bytes / (1024 ** 2)       # Convert bytes to MB
    return mem_mb


class SharedContext:
    cc = None
    publicKey = None

    # Shared common ciphertexts
    mask_one_zeros = None
    ciph_zero = None

    # Crypto Parameters
    level_budget = [2, 2]
    available_levels = 22
    key_dist = SecretKeyDist.SPARSE_TERNARY
    
    mult_depth = available_levels + FHECKKSRNS.GetBootstrapDepth(level_budget, key_dist)
    scale_mod_size = 45
    first_mod_size = 50
    batch_size = 128
    sec_level = SecurityLevel.HEStd_NotSet
    #sec_level = SecurityLevel.HEStd_128_classic

    ring_dim = 0

    offset_x = 0
    offset_y = 0
    scale = 0

    # bounding box for scaling
    def __init__(self):
        pass

    def create_shared_context(self, offset_x: float, offset_y: float, scale: float, levels: int = 22, scaleMod: int = 45, firstMod: int = 50, batch_size: int = 128, sec_level: SecurityLevel = SecurityLevel.HEStd_NotSet) -> PrivateKey:
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.scale = scale

        self.scale_mod_size = scaleMod
        self.first_mod_size = firstMod
        self.batch_size = batch_size
        self.sec_level = sec_level
        self.mult_depth = levels# + FHECKKSRNS.GetBootstrapDepth(self.level_budget, self.key_dist)

        if self.sec_level == SecurityLevel.HEStd_NotSet:
            self.ring_dim = self.batch_size * 2

        if self.cc is not None:
            self.cc.ClearEvalAutomorphismKeys()
        ClearEvalMultKeys()
        ReleaseAllContexts()

        parameters = CCParamsCKKSRNS()
        parameters.SetSecurityLevel(self.sec_level)
        if self.sec_level == SecurityLevel.HEStd_NotSet:
            parameters.SetRingDim(self.ring_dim)
        parameters.SetSecretKeyDist(self.key_dist)
        parameters.SetMultiplicativeDepth(self.mult_depth)
        parameters.SetBatchSize(self.batch_size)
        print(self.scale_mod_size)
        if self.scale_mod_size > 59:
            parameters.SetScalingTechnique(ScalingTechnique.COMPOSITESCALINGAUTO)
            parameters.SetRegisterWordSize(64)
        else:
            parameters.SetScalingTechnique(ScalingTechnique.FLEXIBLEAUTO)
        parameters.SetScalingModSize(self.scale_mod_size)
        parameters.SetFirstModSize(self.first_mod_size)

        self.cc = GenCryptoContext(parameters)
        self.cc.Enable(PKESchemeFeature.PKE)
        self.cc.Enable(PKESchemeFeature.KEYSWITCH)
        self.cc.Enable(PKESchemeFeature.LEVELEDSHE)
        self.cc.Enable(PKESchemeFeature.ADVANCEDSHE)
        self.cc.Enable(PKESchemeFeature.FHE)

        self.ring_dim = self.cc.GetRingDimension()
        print("Crypto Parameters:")
        print("Ring dimension: ", self.ring_dim)
        print("Sec level: ", self.sec_level)
        print("Scale mod size: ", self.scale_mod_size)
        print("First mod size: ", self.first_mod_size)
        print("Batch size: ", self.batch_size)
        print("Mult Depth: ", self.mult_depth, " (", levels, " available")

        self.cc.EvalBootstrapSetup(self.level_budget, [0, 0], self.batch_size)

        keys = self.cc.KeyGen()
        self.cc.EvalMultKeyGen(keys.secretKey)
        self.cc.EvalSumKeyGen(keys.secretKey, keys.publicKey)
        self.cc.EvalBootstrapKeyGen(keys.secretKey, self.batch_size)
        self.cc.EvalRotateKeyGen(keys.secretKey, [1, -1])

        self.publicKey = keys.publicKey
        self.secretKey = keys.secretKey #FOR TESTING

        self.ciph_zero = self.cc.Encrypt(self.publicKey, self.cc.MakeCKKSPackedPlaintext([0]*self.batch_size))
        self.ciph_one = self.cc.Encrypt(self.publicKey, self.cc.MakeCKKSPackedPlaintext([1] * self.batch_size))
        self.mask_one_zeros = self.cc.Encrypt(self.publicKey, self.cc.MakeCKKSPackedPlaintext([1] + [0] * (self.batch_size - 1)))

        return keys.secretKey



_shared_context = None

def create_shared_context(offset_x: float, offset_y: float, scale: float, levels: int = 22, scaleMod: int = 45, firstMod: int = 50, batch_size: int = 128, sec_level: SecurityLevel = SecurityLevel.HEStd_NotSet) -> PrivateKey:
    global _shared_context
    _shared_context = SharedContext()
    secKey = _shared_context.create_shared_context(offset_x, offset_y, scale, levels, scaleMod, firstMod, batch_size, sec_level)

    return secKey

def load_shared_context():
    pass

def get_shared_context() -> SharedContext | None:
    return _shared_context

###############


def debug(msg, *args, **kwargs):
    if getLogger().isEnabledFor(10):  # or logging.DEBUG
        _debug(msg, *args, **kwargs)

def info(msg, *args, **kwargs):
    if getLogger().isEnabledFor(INFO):
        _info(msg, *args, **kwargs)