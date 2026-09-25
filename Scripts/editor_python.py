"""Run project Python in the live editor over its local-only Python SDK connection."""

import argparse
from pathlib import Path
import socket
import sys
import time
import types


ROOT = Path(__file__).resolve().parents[1]
SDK = Path("/Users/Shared/Epic Games/UE_5.8/Engine/Plugins/Experimental/PythonScriptPlugin/Content/Python")


def connect():
    sys.path.insert(0, str(SDK))
    import remote_execution as ue
    config = ue.RemoteExecutionConfig()
    config.multicast_bind_address = "0.0.0.0"
    remote = ue.RemoteExecution(config)
    remote.start()
    broadcast = remote._broadcast_connection
    broadcast._broadcast_socket.setsockopt(
        socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP,
        socket.inet_aton("239.0.0.1") + socket.inet_aton("127.0.0.1"))

    def loopback_send(connection, message):
        connection._broadcast_socket.sendto(message.to_json_bytes(), ("127.0.0.1", 6766))

    broadcast._broadcast_message = types.MethodType(loopback_send, broadcast)
    try:
        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            nodes = [node for node in remote.remote_nodes if node.get("project_name") == "PlatformNine"]
            if len(nodes) > 1:
                raise RuntimeError("Multiple PlatformNine editors; refusing ambiguous execution")
            if nodes:
                remote.open_command_connection(nodes[0]["node_id"])
                remote._command_connection._command_channel_socket.settimeout(600)
                probe = remote.run_command(
                    "__import__('pathlib').Path(unreal.Paths.project_dir()).resolve().as_posix()",
                    exec_mode=ue.MODE_EVAL_STATEMENT, raise_on_failure=True)
                if probe["result"].strip("'\"") != ROOT.as_posix():
                    raise RuntimeError("Editor project root does not match this checkout")
                return remote
            time.sleep(0.2)
        raise RuntimeError("No local PlatformNine Python node. Enable loopback Python remote execution through MCP.")
    except Exception:
        remote.stop()
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("script", type=Path)
    parser.add_argument("arguments", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    script = args.script.resolve()
    if not script.is_relative_to(ROOT) or not script.is_file():
        raise ValueError("Script must be an existing file inside this checkout")
    remote = connect()
    try:
        result = remote.run_command(
            '"' + str(script) + '" ' + " ".join(args.arguments), raise_on_failure=False)
        for entry in result["output"]:
            print(entry["output"], end="")
        if not result["success"] or any(entry["type"] == "Error" for entry in result["output"]):
            raise RuntimeError("Editor Python failed: " + result["result"])
    finally:
        remote.stop()


if __name__ == "__main__":
    main()
