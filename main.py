import argparse
import sys
import time
from pathlib import Path
from typing import List


project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from ai_powered_jenkins_auditor.jenkins_files_parser.Pipeline_manager import PipelineManager
from ai_powered_jenkins_auditor.security_advisor_agent.workflow import app_workflow
from ai_powered_jenkins_auditor.security_advisor_agent.state import AgentState


class AuditOrchestrator:
    """
    Orchestrates the audit process for a collection of Jenkinsfiles.
    """
    def __init__(self, input_dir: Path, output_dir: Path, remediate: bool = False):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.manager = PipelineManager()
        self.jenkins_files: List[Path] = []
       

    def discover_files(self) -> bool:
        """Find all Jenkinsfiles in the input directory."""
        if not self.input_dir.is_dir():
            print(f"!!! ERROR: Input directory not found at '{self.input_dir}'")
            return False

        self.jenkins_files = [
            f for f in self.input_dir.iterdir()
            if f.is_file() and f.suffix.lower() in {".groovy", ".jenkinsfile"}
        ]

        if not self.jenkins_files:
            print(f"No Jenkinsfiles found in '{self.input_dir}'.")
            return False

        print(f"Found {len(self.jenkins_files)} Jenkinsfile(s) to analyze.\n")
        return True

    

    def run(self) -> None:
        """Execute the audit and remediation process."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        start_time = time.time()

        for file_path in self.jenkins_files:
           

            try:
                content = file_path.read_text(encoding="utf-8")
               
            except IOError as e:
                print(f"!!! ERROR: Could not read '{file_path}': {e}")
                continue

        
            
            try:
               
                print("\n Running remediation...")
                audited_pipeline = self.manager.run_remediation(content)   
                if audited_pipeline is None:
                    print(" ERROR: run_remediation returned None!")
                    continue
                    
            except Exception as e:
                print(f"ERROR during remediation: {e}")
                import traceback
                traceback.print_exc()
                continue
            
            if not audited_pipeline.agent and not audited_pipeline.stages:
                warning_message = (
                    f"No valid declarative 'pipeline' block found in {file_path.name}.\n"
                    f"No audit performed."
                )
                print(f"⚠️ {warning_message}")
                self._write_report(
                    self.output_dir / f"{file_path.stem}_report.md",
                    f"# Audit Report for {file_path.name}\n\n {warning_message}"
                )
                continue

        
            
            
            """try:
                initial_state: AgentState = {
                    "pipeline": audited_pipeline,
                    "tasks_to_do": [],
                    "raw_findings": [],
                    "final_report": ""
                }
                
                print("Invoking AI workflow...")
                final_state = app_workflow.invoke(initial_state)
                
                
                print(f" Final state keys: {final_state.keys()}")
                
                final_report = final_state.get(
                    "final_report",
                    f"Error generating report for {file_path.name}"
                )
                
                print(f" Report length: {len(final_report)} characters")
                
                self._write_report(
                    self.output_dir / f"{file_path.stem}_report.md",
                    final_report
                )
                
            except Exception as e:
                print(f" ERROR during workflow execution: {e}")
                import traceback
                traceback.print_exc()
                
                
                error_report = f"# Error Report for {file_path.name}\n\n❌ Error during processing: {str(e)}"
                self._write_report(
                    self.output_dir / f"{file_path.stem}_error_report.md",
                    error_report
                )

        elapsed = time.time() - start_time
        print("\n" + "=" * 60)
        print("Batch audit complete")
        print(f"Processed {len(self.jenkins_files)} files in {elapsed:.2f} seconds.")
        print(f" Reports saved in: '{self.output_dir}'")
        print("=" * 60) """

    def _write_report(self, file_path: Path, content: str) -> None:
        """Write the report content to a file."""
        try:
            file_path.write_text(content, encoding="utf-8")
            print(f"Report saved: {file_path}")
        except IOError as e:
            print(f"!!! ERROR: Could not save report '{file_path}': {e}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="AI-Powered Jenkins Auditor - Audit Jenkinsfiles for security and best practices."
    )
    parser.add_argument(
        "input_dir",
        type=Path,
        nargs='?',
        default=Path("jenkins_files_directory"),
        help="Directory containing Jenkinsfiles (default: jenkins_files_directory)."
    )
    parser.add_argument(
        "-o", "--output-dir",
        type=Path,
        default=Path("audit_reports"),
        help="Directory to save the audit reports (default: audit_reports)."
    )
    parser.add_argument(
        "--remediate",
        action="store_true",
        help="Run the credential remover instead of the AI audit."
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable detailed debugging output."
    )
    args = parser.parse_args()

    print("=" * 60)
    print(" AI-Powered Jenkins Auditor - STARTING")
    print(f" Input Directory: {args.input_dir}")
    print(f" Output Directory: {args.output_dir}")
    print("  Mode: Audit & Remediate" if args.remediate else " Mode: AI-Powered Audit")
    if args.debug:
        print("🔍 Debug mode: ENABLED")
    print("=" * 60)

    orchestrator = AuditOrchestrator(args.input_dir, args.output_dir, args.remediate)
    if orchestrator.discover_files():
        orchestrator.run()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)