
"""
AI-Powered Jenkins Auditor - Main Entry Point

Orchestrates security auditing and remediation of Jenkinsfiles using AI-powered analysis.
Supports single file, batch directory processing, and real-time file watching modes.
"""

import argparse
import sys
import time
from pathlib import Path
from typing import List, Optional, Set, Tuple
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent


# Add project root to Python path for module imports
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from ai_powered_jenkins_auditor.jenkins_files_parser.Pipeline_manager import PipelineManager
from ai_powered_jenkins_auditor.security_advisor_agent.workflow import app_workflow
from ai_powered_jenkins_auditor.security_advisor_agent.state import AgentState


class JenkinsfileHandler(FileSystemEventHandler):
    """
    File system event handler for detecting and processing new Jenkinsfiles.
    
    Handles file creation events with proper readiness checks to avoid race conditions
    during file write operations.
    """
    
    def __init__(self, orchestrator: 'AuditOrchestrator') -> None:
        """
        Initialize the Jenkinsfile handler.
        
        Args:
            orchestrator: Reference to the main AuditOrchestrator instance
        """
        self.orchestrator = orchestrator
        self.processed_files: Set[str] = set()  # Track processed files to avoid duplicates
    
    def on_created(self, event: FileCreatedEvent) -> None:
        """
        Handle file creation events.
        
        Args:
            event: File system event containing creation details
        """
        if not event.is_directory:
            file_path = Path(event.src_path)
            if (self._is_jenkinsfile(file_path) and 
                file_path.name not in self.processed_files):
                print(f"New Jenkinsfile detected: {file_path.name}")
                if self._wait_for_file_ready(file_path):
                    self.processed_files.add(file_path.name)
                    self.orchestrator.process_single_file(file_path)
    
    def _is_jenkinsfile(self, file_path: Path) -> bool:
        """
        Determine if a file is a Jenkinsfile based on naming conventions.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            bool: True if file appears to be a Jenkinsfile, False otherwise
        """
        lower_name = file_path.name.lower()
        valid_extensions = {".groovy", ".jenkinsfile"}
        return (file_path.suffix.lower() in valid_extensions or
                lower_name == "jenkinsfile" or
                lower_name.endswith(".jenkinsfile"))
    
    def _wait_for_file_ready(self, file_path: Path, 
                           max_attempts: int = 10, 
                           delay: float = 0.5) -> bool:
        """
        Wait for a file to be fully written and ready for processing.
        
        Args:
            file_path: Path to the file to check
            max_attempts: Maximum number of readiness checks
            delay: Delay between checks in seconds
            
        Returns:
            bool: True if file is ready, False if timeout reached
        """
        for attempt in range(max_attempts):
            try:
                # Check if file exists and has content
                if file_path.exists() and file_path.stat().st_size > 0:
                    # Test file readability
                    with open(file_path, 'r', encoding='utf-8') as f:
                        f.read(1)  # Read first character to test lock status
                    print(f"File {file_path.name} is ready for processing")
                    return True
            except (IOError, PermissionError, OSError) as e:
                # File might still be being written
                if attempt < max_attempts - 1:
                    time.sleep(delay)
                    continue
                else:
                    print(f"File {file_path.name} never became readable: {e}")
                    return False
            except Exception as e:
                print(f"Unexpected error checking file {file_path.name}: {e}")
                return False
        
        print(f"File {file_path.name} not ready after {max_attempts} attempts")
        return False


class AuditOrchestrator:
    """
    Orchestrates the Jenkinsfile audit process across multiple operating modes.
    
    Provides functionality for single file processing, batch directory processing,
    and real-time file watching with automated auditing.
    """
    
    def __init__(self, input_dir: Path, output_dir: Path, remediate: bool = False) -> None:
        """
        Initialize the audit orchestrator.
        
        Args:
            input_dir: Directory or file to process
            output_dir: Directory for audit reports
            remediate: Whether to run credential remediation
        """
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.remediate = remediate
        self.manager = PipelineManager()
        self.jenkins_files: List[Path] = []
        self.observer: Optional[Observer] = None

    def discover_files(self) -> bool:
        """
        Discover all Jenkinsfiles in the input directory.
        
        Returns:
            bool: True if files were found, False otherwise
        """
        if not self.input_dir.is_dir():
            print(f"ERROR: Input directory not found at '{self.input_dir}'")
            return False

        self.jenkins_files = [
            f for f in self.input_dir.iterdir()
            if f.is_file() and self._is_jenkinsfile(f)
        ]

        if not self.jenkins_files:
            print(f"No Jenkinsfiles found in '{self.input_dir}'.")
            return False

        print(f"Found {len(self.jenkins_files)} Jenkinsfile(s) to analyze.")
        return True

    def _is_jenkinsfile(self, file_path: Path) -> bool:
        """
        Check if a file is a Jenkinsfile based on naming conventions.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            bool: True if file appears to be a Jenkinsfile
        """
        lower_name = file_path.name.lower()
        valid_extensions = {".groovy", ".jenkinsfile"}
        return (file_path.suffix.lower() in valid_extensions or
                lower_name == "jenkinsfile" or
                lower_name.endswith(".jenkinsfile"))

    def process_single_file(self, file_path: Path) -> bool:
        """
        Process a single Jenkinsfile through the complete audit pipeline.
        
        Args:
            file_path: Path to the Jenkinsfile to process
            
        Returns:
            bool: True if processing completed successfully, False otherwise
        """
        print(f"Processing: {file_path.name}")
        
        # Validate file existence
        if not file_path.exists():
            print(f"File disappeared during processing: {file_path.name}")
            return False
        
        # Read and validate file content
        try:
            content = file_path.read_text(encoding="utf-8")
            if not content.strip():
                print(f"File is empty: {file_path.name}")
                self._write_report(
                    self.output_dir / f"{file_path.stem}_report.md",
                    f"# Audit Report for {file_path.name}\n\nFile is empty - no content to audit."
                )
                return True
        except IOError as e:
            print(f"Could not read '{file_path}': {e}")
            return False
        except UnicodeDecodeError as e:
            print(f"Encoding error reading '{file_path}': {e}")
            self._write_report(
                self.output_dir / f"{file_path.stem}_error_report.md",
                f"# Error Report for {file_path.name}\n\nFile encoding error: {str(e)}"
            )
            return False

        print(f"File size: {len(content)} characters")
        
        # Run remediation phase
        try:
            print("Running remediation...")
            audited_pipeline = self.manager.run_remediation(content)   
            if audited_pipeline is None:
                print("ERROR: Remediation process returned None")
                self._write_report(
                    self.output_dir / f"{file_path.stem}_error_report.md",
                    f"# Error Report for {file_path.name}\n\nRemediation process failed - possible parsing error."
                )
                return False
                
            print(f"Remediation completed for {file_path.name}")
            
        except Exception as e:
            print(f"ERROR during remediation: {e}")
            import traceback
            traceback.print_exc()
            self._write_report(
                self.output_dir / f"{file_path.stem}_error_report.md",
                f"# Error Report for {file_path.name}\n\nRemediation error: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
            )
            return False
        
        # Validate pipeline structure
        if not audited_pipeline.agent and not audited_pipeline.stages:
            warning_message = (
                f"No valid declarative 'pipeline' block found in {file_path.name}.\n"
                f"This might be a scripted pipeline or invalid Jenkinsfile."
            )
            print(f"Warning: {warning_message}")
            self._write_report(
                self.output_dir / f"{file_path.stem}_report.md",
                f"# Audit Report for {file_path.name}\n\n{warning_message}\n\n## File Content:\n```groovy\n{content}\n```"
            )
            return True

        # Execute AI workflow
        try:
            print("Invoking AI workflow...")
            initial_state: AgentState = {
                "pipeline": audited_pipeline,
                "tasks_to_do": [],
                "raw_findings": [],
                "final_report": ""
            }
            
            final_state = app_workflow.invoke(initial_state)
            
            final_report = final_state.get(
                "final_report",
                f"# Error Report for {file_path.name}\n\nAI workflow did not generate a report."
            )
            
            self._write_report(
                self.output_dir / f"{file_path.stem}_report.md",
                final_report
            )
            print(f"Completed: {file_path.name}")
            return True
            
        except Exception as e:
            print(f"ERROR during workflow execution: {e}")
            import traceback
            traceback.print_exc()
            
            error_report = f"# Error Report for {file_path.name}\n\nError during AI workflow: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
            self._write_report(
                self.output_dir / f"{file_path.stem}_error_report.md",
                error_report
            )
            return False

    def run_single_file(self, file_path: Path) -> None:
        """
        Execute audit for a single Jenkinsfile with comprehensive reporting.
        
        Args:
            file_path: Path to the Jenkinsfile to audit
        """
        if not file_path.exists():
            print(f"ERROR: File not found: '{file_path}'")
            return
        
        if not self._is_jenkinsfile(file_path):
            print(f"ERROR: '{file_path}' does not appear to be a Jenkinsfile")
            return

        self.output_dir.mkdir(parents=True, exist_ok=True)
        start_time = time.time()

        success = self.process_single_file(file_path)

        elapsed = time.time() - start_time
        print("\n" + "=" * 60)
        print("Single file audit complete")
        print(f"Processed 1 file in {elapsed:.2f} seconds.")
        print(f"Status: {'SUCCESS' if success else 'FAILED'}")
        print(f"Report saved in: '{self.output_dir}'")
        print("=" * 60)

    def run_batch(self) -> None:
        """
        Execute batch audit for all discovered Jenkinsfiles in the input directory.
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)
        start_time = time.time()
        success_count = 0

        for file_path in self.jenkins_files:
            if self.process_single_file(file_path):
                success_count += 1

        elapsed = time.time() - start_time
        print("\n" + "=" * 60)
        print("Batch audit complete")
        print(f"Processed {len(self.jenkins_files)} files ({success_count} successful) in {elapsed:.2f} seconds.")
        print(f"Reports saved in: '{self.output_dir}'")
        print("=" * 60)

    def start_watching(self) -> None:
        """
        Start watching the input directory for new Jenkinsfiles and process them automatically.
        """
        if not self.input_dir.is_dir():
            print(f"ERROR: Input directory not found at '{self.input_dir}'")
            return

        print(f"Starting file watcher on: {self.input_dir}")
        print("Press Ctrl+C to stop watching...")
        print("=" * 60)

        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Process existing files first
        if self.discover_files():
            self.run_batch()

        # Set up file watcher
        event_handler = JenkinsfileHandler(self)
        self.observer = Observer()
        self.observer.schedule(event_handler, str(self.input_dir), recursive=False)
        self.observer.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping file watcher...")
        finally:
            if self.observer:
                self.observer.stop()
                self.observer.join()

    def _write_report(self, file_path: Path, content: str) -> None:
        """
        Write audit report content to a file with comprehensive error handling.
        
        Args:
            file_path: Path where the report should be saved
            content: Report content to write
        """
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
            print(f"Report saved: {file_path.name}")
        except IOError as e:
            print(f"ERROR: Could not save report '{file_path}': {e}")
            # Fallback to temporary directory
            try:
                fallback_path = Path("/tmp") / file_path.name
                fallback_path.write_text(content, encoding="utf-8")
                print(f"Saved report to fallback location: {fallback_path}")
            except Exception as fallback_error:
                print(f"CRITICAL: Could not save report anywhere: {fallback_error}")


def main() -> None:
    """
    Main entry point for the AI-Powered Jenkins Auditor.
    
    Parses command line arguments and orchestrates the audit process
    based on the selected operating mode.
    """
    parser = argparse.ArgumentParser(
        description="AI-Powered Jenkins Auditor - Audit Jenkinsfiles for security and best practices.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s pipeline.jenkinsfile --single    # Audit single file
  %(prog)s jenkins_files/                   # Batch process directory
  %(prog)s jenkins_files/ --watch           # Watch directory for new files
  %(prog)s --help                           # Show this help message
        """
    )
    
    parser.add_argument(
        "input",
        nargs='?',
        help="Input file or directory. File for single mode, directory for batch/watch mode."
    )
    parser.add_argument(
        "-o", "--output-dir",
        type=Path,
        default=Path("audit_reports"),
        help="Directory to save audit reports (default: audit_reports)"
    )
    parser.add_argument(
        "--remediate",
        action="store_true",
        help="Run credential remediation instead of full AI audit"
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Watch directory for new Jenkinsfiles and process automatically"
    )
    parser.add_argument(
        "--single",
        action="store_true",
        help="Process a single file (input must be a file path)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable detailed debugging output"
    )
    
    args = parser.parse_args()

    # Set default input if not provided
    if args.input is None:
        if args.single:
            print("ERROR: Single file mode requires an input file path")
            sys.exit(1)
        input_path = Path("jenkins_files_directory")
    else:
        input_path = Path(args.input)

    print("=" * 60)
    print("AI-Powered Jenkins Auditor - STARTING")
    print(f"Input: {input_path}")
    print(f"Output Directory: {args.output_dir}")
    
    mode = "Audit & Remediate" if args.remediate else "AI-Powered Audit"
    print(f"Mode: {mode}")
    
    if args.single:
        operation = "Single File"
    elif args.watch:
        operation = "Directory Watching"
    else:
        operation = "Batch Processing"
    print(f"Operation: {operation}")
        
    if args.debug:
        print("Debug mode: ENABLED")
    print("=" * 60)

    orchestrator = AuditOrchestrator(input_path, args.output_dir, args.remediate)
    
    if args.single:
        # Single file mode
        if input_path.is_dir():
            print("ERROR: Single file mode requires a file, not a directory")
            sys.exit(1)
        orchestrator.run_single_file(input_path)
    elif args.watch:
        # Watch mode - requires directory
        if not input_path.is_dir():
            print("ERROR: Watch mode requires a directory")
            sys.exit(1)
        orchestrator.start_watching()
    else:
        # Batch mode - can be file or directory
        if input_path.is_file():
            # If input is a file, run single file mode
            orchestrator.run_single_file(input_path)
        else:
            # If input is a directory, run batch mode
            if orchestrator.discover_files():
                orchestrator.run_batch()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)