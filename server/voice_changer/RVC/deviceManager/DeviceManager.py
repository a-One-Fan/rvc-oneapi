import torch
import onnxruntime

from voice_changer.utils.Device import get_per_api_device_count, get_a_device, get_per_api_device_properties, get_per_api_device_name

class DeviceManager(object):
    _instance = None
    forceTensor: bool = False

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.gpu_num = get_per_api_device_count()
        self.mps_enabled: bool = (
            getattr(torch.backends, "mps", None) is not None
            and torch.backends.mps.is_available()
        )

    def getDevice(self, id: int):
        if id < 0 or self.gpu_num == 0:
            if self.mps_enabled is False:
                dev = torch.device("cpu")
            else:
                dev = torch.device("mps")
        else:
            if id < self.gpu_num:
                dev = torch.device(get_a_device(), index=id)
            else:
                print("[Voice Changer] device detection error, fallback to cpu")
                dev = torch.device("cpu")
        return dev

    def getOnnxExecutionProvider(self, gpu: int):
        availableProviders = onnxruntime.get_available_providers()
        devNum = get_per_api_device_count()
        print("\n\nCUDA ONNX execution provider? 3\n\n")
        if gpu >= 0 and "CUDAExecutionProvider" in availableProviders and devNum > 0:
            if gpu < devNum:  # ひとつ前のif文で弾いてもよいが、エラーの解像度を上げるため一段下げ。
                return ["CUDAExecutionProvider"], [{"device_id": gpu}]
            else:
                print("[Voice Changer] device detection error, fallback to cpu")
                return ["CPUExecutionProvider"], [
                    {
                        "intra_op_num_threads": 8,
                        "execution_mode": onnxruntime.ExecutionMode.ORT_PARALLEL,
                        "inter_op_num_threads": 8,
                    }
                ]
        elif gpu >= 0 and "DmlExecutionProvider" in availableProviders:
            return ["DmlExecutionProvider"], [{"device_id": gpu}]
        else:
            return ["CPUExecutionProvider"], [
                {
                    "intra_op_num_threads": 8,
                    "execution_mode": onnxruntime.ExecutionMode.ORT_PARALLEL,
                    "inter_op_num_threads": 8,
                }
            ]

    def setForceTensor(self, forceTensor: bool):
        self.forceTensor = forceTensor

    def halfPrecisionAvailable(self, id: int):
        if self.gpu_num == 0:
            return False
        if id < 0:
            return False
        if self.forceTensor:
            return False

        try:
            gpuName = get_per_api_device_name(id).upper()
            if (
                ("16" in gpuName and "V100" not in gpuName)
                or "P40" in gpuName.upper()
                or "1070" in gpuName
                or "1080" in gpuName
            ):
                return False
        except Exception as e:
            print(e)
            return False

        return True

    def getDeviceMemory(self, id: int):
        try:
            return get_per_api_device_properties(id).total_memory
        except Exception as e:
            # except:
            print(e)
            return 0
