import json
import requests
from websocket import WebSocket
import uuid

class JupyterClient:
    def __init__(self, base_url, token):
        """
        Initialize Jupyter client with server URL and authentication token

        Args:
            base_url (str): Base URL of Jupyter server (e.g., 'http://localhost:8888')
            token (str): Authentication token
        """
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.session_id = str(uuid.uuid4())
        self.kernel_id = None

        # Create kernel
        self.start_kernel()

        # Setup WebSocket connection
        ws_url = f"{self.base_url.replace('http', 'ws')}/api/kernels/{self.kernel_id}/channels"
        self.ws = WebSocket()
        self.ws.connect(
            ws_url + f"?token={self.token}",
            header={"Authorization": f"token {self.token}"}
        )

    def start_kernel(self):
        """Start a new SageMath kernel"""
        response = requests.post(
            f"{self.base_url}/api/kernels",
            params={"token": self.token},
            headers={"Authorization": f"token {self.token}"},
            json={"name": "sagemath"}
        )
        response.raise_for_status()
        self.kernel_id = response.json()["id"]

    def execute_code(self, code):
        """
        Execute code in the SageMath kernel

        Args:
            code (str): Code to execute

        Returns:
            dict: Execution results
        """
        # Send execute request
        msg_id = str(uuid.uuid4())
        execute_request = {
            "header": {
                "msg_id": msg_id,
                "username": "client",
                "session": self.session_id,
                "msg_type": "execute_request",
                "version": "5.0"
            },
            "parent_header": {},
            "metadata": {},
            "content": {
                "code": code,
                "silent": False,
                "store_history": True,
                "user_expressions": {},
                "allow_stdin": False
            },
            "channel": "shell"
        }

        self.ws.send(json.dumps(execute_request))

        # Collect output until we get execute_reply
        outputs = []
        while True:
            response = json.loads(self.ws.recv())

            if response["header"]["msg_type"] == "execute_reply":
                break

            if response["header"]["msg_type"] == "stream":
                outputs.append(response["content"]["text"])
            elif response["header"]["msg_type"] == "execute_result":
                outputs.append(str(response["content"]["data"].get("text/plain", "")))
            elif response["header"]["msg_type"] == "error":
                raise Exception("\n".join(response["content"]["traceback"]))

        return "".join(outputs)

    def close(self):
        """Clean up connections"""
        self.ws.close()
        requests.delete(
            f"{self.base_url}/api/kernels/{self.kernel_id}",
            params={"token": self.token},
            headers={"Authorization": f"token {self.token}"}
        )
