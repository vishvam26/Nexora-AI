"""
PythonAgent — Step 14 Python Execution Agent

Executes Python data analysis code (Pandas, NumPy, Matplotlib) inside a
restricted subprocess sandbox. Surfacess stdout outputs and generated plots.
"""
import os
import re
import sys
import uuid
import logging
import subprocess
from typing import Dict, Any

from app.services.agents.base_agent import BaseAgent, AgentContext, AgentResult

logger = logging.getLogger("app.services.agents.python_agent")

PLOT_DIR = os.path.join("storage", "reports")
os.makedirs(PLOT_DIR, exist_ok=True)


class PythonAgent(BaseAgent):
    name = "python_agent"
    description = (
        "Runs python scripts to analyze local datasets using Pandas, NumPy, and Matplotlib. "
        "Allows plotting charts, calculating custom formulas, grouping data, and statistical sorting. "
        "Invoke when the CEO's question requires custom data manipulation, charting, plotting, or coding."
    )

    def run(self, task: str, context: AgentContext) -> AgentResult:
        if not context.file_path:
            return AgentResult.skipped(
                self.name, task,
                "No dataset file_path provided. Python agent requires a tabular dataset."
            )

        tool_calls = []
        output: Dict[str, Any] = {}
        summaries = []

        # Extract python code block from task or construct one dynamically
        code_match = re.search(r"```python\s*(.*?)\s*```", task, re.DOTALL | re.IGNORECASE)
        code_to_run = code_match.group(1) if code_match else task

        # Security Sandbox Checklist Check
        forbidden = [
            r"\bos\b", r"\bsys\b", r"\bsubprocess\b", r"\bshutil\b",
            r"\bbuiltins\b", r"\bopen\b", r"\beval\b", r"\bexec\b",
            r"\b__import__\b", r"\bimportlib\b"
        ]
        for pattern in forbidden:
            if re.search(pattern, code_to_run):
                return AgentResult.error_result(
                    self.name, task,
                    f"Security Block: Forbidden module or function pattern detected: {pattern}"
                )

        # Generate a unique chart file name in case plt.savefig is used
        chart_id = f"plot_{uuid.uuid4().hex[:12]}"
        chart_filename = f"{chart_id}.png"
        chart_filepath = os.path.join(PLOT_DIR, chart_filename)

        # Resolve relative storage paths to absolute paths under "uploads/knowledge"
        file_path = context.file_path
        if not os.path.isabs(file_path):
            file_path = os.path.abspath(os.path.join("uploads", "knowledge", file_path))

        # Format DF_PATH using forward slashes for safety
        formatted_df_path = file_path.replace("\\", "/")

        # Prepare code wrapper to auto-load dataset and override savefig target
        wrapper_code = f"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

DF_PATH = "{formatted_df_path}"
df = pd.read_csv(DF_PATH)

# Override plt.show to redirect plot outputs to a static image
def show_override():
    plt.savefig("{chart_filepath.replace("\\", "/")}", bbox_inches='tight', dpi=150)
    plt.close()
plt.show = show_override

# User generated code:
{code_to_run}

# Auto-save plot if figures exist and plt.show wasn't called explicitly
if len(plt.get_fignums()) > 0:
    show_override()
"""

        # Execute code wrapper in a separate python process
        logger.info("[PythonAgent] Executing python sandbox query...")
        try:
            # We run the script inside a subprocess wrapper to isolate execution state
            result = subprocess.run(
                [sys.executable, "-c", wrapper_code],
                capture_output=True,
                text=True,
                timeout=20 # 20 second timeout safeguard
            )
            tool_calls.append("subprocess.run")

            stdout_out = result.stdout.strip()
            stderr_out = result.stderr.strip()

            output["stdout"] = stdout_out
            output["stderr"] = stderr_out
            output["return_code"] = result.returncode

            if result.returncode == 0:
                summaries.append("Python script executed successfully inside sandbox.")
                if stdout_out:
                    summaries.append(f"Console Output: {stdout_out[:200]}...")
                
                # Check if matplotlib saved a plot file
                if os.path.exists(chart_filepath):
                    # Save local relative path for API mapping access
                    output["chart_path"] = f"/reports/{chart_filename}"
                    output["chart_id"] = chart_id
                    summaries.append(f"Visualization plot exported as {chart_filename}.")
            else:
                summaries.append(f"Python script execution failed with code {result.returncode}.")
                return AgentResult.error_result(self.name, task, f"Script stderr: {stderr_out}")

        except subprocess.TimeoutExpired:
            return AgentResult.error_result(self.name, task, "Execution timeout: Script exceeded 20s limit.")
        except Exception as e:
            return AgentResult.error_result(self.name, task, f"Sandbox launch error: {str(e)}")

        return AgentResult(
            agent_name=self.name,
            task=task,
            status="success",
            output=output,
            summary=" ".join(summaries),
            tool_calls=tool_calls
        )

    def get_tool_definition(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task": {
                            "type": "string",
                            "description": "The complete Python code block to execute against the loaded DataFrame. Load path is automatically set as global DF_PATH variable."
                        }
                    },
                    "required": ["task"]
                }
            }
        }
