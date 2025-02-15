# Copyright (c) 2022 PaddlePaddle Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from trt_layer_auto_scan_test import TrtLayerAutoScanTest
from program_config import TensorConfig, ProgramConfig
import numpy as np
import paddle.inference as paddle_infer
from functools import partial
from typing import List
import unittest


class TrtConvertScatterNd(TrtLayerAutoScanTest):

    def is_program_valid(self, program_config: ProgramConfig) -> bool:
        return True

    def sample_program_configs(self):

        def generate_input1():
            return np.random.random([6]).astype(np.float32)

        def generate_input2():
            return np.random.random([4, 1]).astype(np.int32)

        def generate_input3():
            return np.random.random([4]).astype(np.float32)

        ops_config = [{
            "op_type": "scatter_nd_add",
            "op_inputs": {
                "X": ["input_data"],
                "Index": ["index_data"],
                "Updates": ["update_data"]
            },
            "op_outputs": {
                "Out": ["output_data"]
            },
            "op_attrs": {}
        }]
        ops = self.generate_op_config(ops_config)
        for i in range(10):
            program_config = ProgramConfig(
                ops=ops,
                weights={},
                inputs={
                    "input_data":
                    TensorConfig(data_gen=partial(generate_input1)),
                    "index_data":
                    TensorConfig(data_gen=partial(generate_input2)),
                    "update_data":
                    TensorConfig(data_gen=partial(generate_input3)),
                },
                outputs=["output_data"])

            yield program_config

    def sample_predictor_configs(
            self, program_config) -> (paddle_infer.Config, List[int], float):

        def generate_dynamic_shape(attrs):
            self.dynamic_shape.min_input_shape = {
                "input_data": [1],
                "index_data": [2, 1],
                "update_data": [1],
            }
            self.dynamic_shape.max_input_shape = {
                "input_data": [6],
                "index_data": [4, 1],
                "update_data": [4],
            }
            self.dynamic_shape.opt_input_shape = {
                "input_data": [6],
                "index_data": [4, 1],
                "update_data": [4],
            }

        def clear_dynamic_shape():
            self.dynamic_shape.max_input_shape = {}
            self.dynamic_shape.min_input_shape = {}
            self.dynamic_shape.opt_input_shape = {}

        attrs = [
            program_config.ops[i].attrs for i in range(len(program_config.ops))
        ]

        # for static_shape
        clear_dynamic_shape()
        self.trt_param.precision = paddle_infer.PrecisionType.Float32
        yield self.create_inference_config(), (0, 5), 1e-5
        self.trt_param.precision = paddle_infer.PrecisionType.Half
        yield self.create_inference_config(), (0, 5), 1e-5

        # for dynamic_shape
        generate_dynamic_shape(attrs)
        self.trt_param.precision = paddle_infer.PrecisionType.Float32
        yield self.create_inference_config(), (1, 4), 1e-5
        self.trt_param.precision = paddle_infer.PrecisionType.Half
        yield self.create_inference_config(), (1, 4), 1e-5

    def test(self):
        self.run_test()


if __name__ == "__main__":
    unittest.main()
