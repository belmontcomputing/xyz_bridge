################################################################################
# Mock-up bridge script for testing purpose.
################################################################################

import os
import logging
import trace

## TODO: Change edatool to tool_bridge!!!
## from edalize.tool_bridge import ToolBridge
from edalize.edatool import Edatool

logger = logging.getLogger(__name__)


#class XyzBridge(ToolBridge):
class Xyz(Edatool):

    argtypes = []
    tool_options = {}

    def _dump(self, I=""):
        """
        """
        print(f'{I}- Xyz(Bridge) object:')
        I += '   '
        for k, v in sorted(self.__dict__.items(), key=lambda x: x[0]):
            if k.endswith('env'):
                continue
            if v is None:
                print(f'{I}- {k}: None')
            elif isinstance(v, dict):
                if len(v) == 0:
                    print(f'{I}- {k}: {{}}')
                else:
                    print(f'{I}- {k}:')
                    [print(f'{I}   - {k2}: {self._param_value_str(v2)}')
                        for k2, v2 in v.items()]
            elif isinstance(v, list):
                if len(v) == 0:
                    print(f'{I}- {k}: []')
                else:
                    print(f'{I}- {k}:')
                    [print(f'{I}   - {v2}') for v2 in v]
            else:
                print(f'{I}- {k}: {str(v)}')
        print('', flush=True)

    def configure_main(self):
        # Dump object for debug purpose.
        # self._dump()

        (src_files, incdirs) = self._get_fileset_files() 

        filelist_file = os.path.join(self.work_root, self.name + '.f')
        fh = open(filelist_file, 'w')

        for f in src_files:
            # Only write out .sv files.
            if f.file_type in ('verilogSource', 'systemVerilogSource'):
                # Skip included files.
                if hasattr(f, 'is_include_file'):
                    continue

                # Compose the line by adding tokens.
                tokens = []
                if f.file_type == 'systemVerilogSource':
                    tokens.append('-sv')
                if f.logical_name:
                    tokens.append(f'-lib {f.logical_name}')
                for k, v in self.vlogdefine.items():
                    tokens.append(f'+define+{k}={self._param_value_str(v)}')
                for k, v in self.vlogparam.items():
                    tokens.append(f'{k}={self._param_value_str(v)}')
                for v in incdirs:
                    tokens.append(f'+incdir+{v}')
                tokens.append(f.name)

                fh.write(' '.join(tokens) + '\n')

        fh.close()
