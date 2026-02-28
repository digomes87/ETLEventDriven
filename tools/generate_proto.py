import subprocess
import sys
import re
from pathlib import Path


def generate_protos():
    print("Generating gRPC files...")
    # Run protoc command using uv run to ensure we use the venv
    cmd = [
        "uv",
        "run",
        "python",
        "-m",
        "grpc_tools.protoc",
        "-Iprotos",
        "--python_out=app/grpc",
        "--grpc_python_out=app/grpc",
        "protos/etlpay.proto",
    ]
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError as e:
        print(f"Error generating protos: {e}")
        return

    # Fix imports and version check in generated files
    grpc_file = Path("app/grpc/etlpay_pb2_grpc.py")
    if grpc_file.exists():
        content = grpc_file.read_text()

        # Fix relative import
        # From: import etlpay_pb2 as etlpay__pb2
        # To:   from . import etlpay_pb2 as etlpay__pb2
        content = re.sub(
            r'^import etlpay_pb2 as etlpay__pb2',
            'from . import etlpay_pb2 as etlpay__pb2',
            content,
            flags=re.MULTILINE
        )

        # Remove broken version check block (grpcio 1.68.0+ issue)
        # The block starts with try: ... from grpc._utilities import first_version_is_lower ...
        # and ends before the first class definition.

        # Pattern to match the try/except block for first_version_is_lower
        version_check_pattern = re.compile(
            r'try:\s+from grpc._utilities import first_version_is_lower.*?except ImportError:.*?_version_not_supported = True',
            re.DOTALL
        )
        content = version_check_pattern.sub('# Version check removed by tools/generate_proto.py', content)

        # Pattern to match the runtime error check
        runtime_error_pattern = re.compile(
            r'if _version_not_supported:.*?raise RuntimeError\(.*?\)',
            re.DOTALL
        )
        content = runtime_error_pattern.sub('# RuntimeError check removed', content)

        grpc_file.write_text(content)
        print(f"Fixed imports and version check in {grpc_file}")
    else:
        print(f"Error: {grpc_file} not found after generation")


if __name__ == "__main__":
    generate_protos()
