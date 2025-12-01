#!/usr/bin/env python3
"""
Phase 1: Critical Validation - @file and /command Testing

CRITICAL PHASE: Tests whether @file, @directory, and /commands work
when GCLI is invoked with -p flag (non-interactive mode).

This validates the entire project's feasibility.
"""

import subprocess
import sys
import json
from pathlib import Path
import time


class Colors:
    """ANSI color codes"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


class Phase1Validator:
    """Tests critical @file and /command functionality"""
    
    def __init__(self):
        self.results = {
            'at_file_works': False,
            'at_file_multiple_works': False,
            'at_directory_works': False,
            'slash_commands_work': None,  # True/False/None (not tested)
            'working_directory_respected': False,
            'stream_json_works': False,
            'tests': []
        }
        
        # Load Phase 0 results
        phase0_file = Path('docs/phase0_results.json')
        if phase0_file.exists():
            with open(phase0_file) as f:
                self.phase0 = json.load(f)
        else:
            print(f"{Colors.RED}ERROR: Run phase0_validate.py first!{Colors.END}")
            sys.exit(1)
        
        self.flag = self.phase0['non_interactive_flag']
        self.test_dir = Path('test-project')
    
    def run_all_tests(self) -> dict:
        """Execute all Phase 1 tests"""
        print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
        print(f"{Colors.BOLD}Phase 1: Critical Validation - @file and /commands{Colors.END}")
        print(f"{Colors.BOLD}{'='*60}{Colors.END}\n")
        
        print(f"{Colors.BLUE}Configuration:{Colors.END}")
        print(f"  GCLI Version: {self.phase0['version']}")
        print(f"  Non-interactive flag: {self.flag}")
        print(f"  Test directory: {self.test_dir}")
        print()
        
        # Verify test directory exists
        if not self.test_dir.exists():
            print(f"{Colors.RED}ERROR: Test project not found at {self.test_dir}{Colors.END}")
            print("Run phase0_validate.py first to create it.")
            sys.exit(1)
        
        # Test 1: @file with single file
        self._test_at_file_single()
        
        # Test 2: @file with multiple files
        self._test_at_file_multiple()
        
        # Test 3: @directory
        self._test_at_directory()
        
        # Test 4: Working directory context
        self._test_working_directory()
        
        # Test 5: /commands (exploratory)
        self._test_slash_commands()
        
        # Test 6: Stream-JSON with @file
        self._test_stream_json()
        
        # Generate report
        self._generate_report()
        
        return self.results
    
    def _test_at_file_single(self):
        """Test: @file loads single file contents"""
        print(f"{Colors.BLUE}[Test 1]{Colors.END} Testing @file with single file...")
        
        prompt = "Explain this code: @src/main.py"
        
        result = self._run_gcli(prompt, cwd=self.test_dir)
        
        test_result = {
            'name': '@file single file',
            'prompt': prompt,
            'success': False,
            'evidence': None
        }
        
        if result['success']:
            output = result['output'].lower()
            
            # Check if response references actual code from main.py
            indicators = [
                'hello_world' in output,
                'print' in output,
                'def ' in output or 'function' in output,
                'main.py' in output
            ]
            
            if any(indicators):
                test_result['success'] = True
                test_result['evidence'] = f"Response references code: {result['output'][:150]}..."
                self.results['at_file_works'] = True
                self._print_success("@file works! Model saw file contents")
                print(f"  Evidence: {', '.join([i for i, v in zip(['hello_world', 'print', 'function', 'main.py'], indicators) if v])}")
            else:
                test_result['evidence'] = "Response doesn't reference file contents"
                self._print_error("@file might not work - no code references found")
                print(f"  Response: {result['output'][:200]}")
        else:
            test_result['evidence'] = result.get('error', 'Command failed')
            self._print_error(f"GCLI command failed: {result.get('error')}")
        
        self.results['tests'].append(test_result)
        print()
    
    def _test_at_file_multiple(self):
        """Test: @file with multiple files"""
        print(f"{Colors.BLUE}[Test 2]{Colors.END} Testing @file with multiple files...")
        
        prompt = "Compare @src/main.py and @docs/README.md. What are the differences?"
        
        result = self._run_gcli(prompt, cwd=self.test_dir)
        
        test_result = {
            'name': '@file multiple files',
            'prompt': prompt,
            'success': False,
            'evidence': None
        }
        
        if result['success']:
            output = result['output'].lower()
            
            # Check references to both files
            has_py = 'main.py' in output or 'hello_world' in output or 'python' in output
            has_md = 'readme' in output or 'markdown' in output or 'documentation' in output
            
            if has_py and has_md:
                test_result['success'] = True
                test_result['evidence'] = "Response references both files"
                self.results['at_file_multiple_works'] = True
                self._print_success("Multiple @file references work!")
            else:
                test_result['evidence'] = f"Missing references (py={has_py}, md={has_md})"
                self._print_warning("Partial success - only some files referenced")
        else:
            test_result['evidence'] = result.get('error')
            self._print_error(f"Command failed: {result.get('error')}")
        
        self.results['tests'].append(test_result)
        print()
    
    def _test_at_directory(self):
        """Test: @directory lists directory contents"""
        print(f"{Colors.BLUE}[Test 3]{Colors.END} Testing @directory...")
        
        prompt = "What files are in @src? List them."
        
        result = self._run_gcli(prompt, cwd=self.test_dir)
        
        test_result = {
            'name': '@directory',
            'prompt': prompt,
            'success': False,
            'evidence': None
        }
        
        if result['success']:
            output = result['output'].lower()
            
            # Check if main.py is mentioned
            if 'main.py' in output:
                test_result['success'] = True
                test_result['evidence'] = "Response mentions main.py"
                self.results['at_directory_works'] = True
                self._print_success("@directory works!")
            else:
                test_result['evidence'] = "main.py not mentioned in response"
                self._print_warning("@directory may not work as expected")
                print(f"  Response: {result['output'][:200]}")
        else:
            test_result['evidence'] = result.get('error')
            self._print_error(f"Command failed: {result.get('error')}")
        
        self.results['tests'].append(test_result)
        print()

    def _test_working_directory(self):
            """Test: Working directory context is respected"""
            print(f"{Colors.BLUE}[Test 4]{Colors.END} Testing working directory context...")

            # Run from project root vs from test-project
            prompt = "@sample.txt - what does this file contain?"

            # Should work when cwd is test-project
            result1 = self._run_gcli(prompt, cwd=self.test_dir)

            # Should fail when cwd is project root (file doesn't exist there)
            result2 = self._run_gcli(prompt, cwd=Path.cwd())

            test_result = {
                'name': 'working directory context',
                'prompt': prompt,
                'success': False,
                'evidence': None
            }

            # Safe access to output
            output1 = result1.get('output', '')
            output2 = result2.get('output', '')
            
            works_in_test_dir = result1['success'] and 'sample' in output1.lower()
            fails_in_root = not result2['success'] or 'cannot' in output2.lower() or 'not found' in output2.lower()

            if works_in_test_dir:
                test_result['success'] = True
                test_result['evidence'] = "File found when cwd is correct"
                self.results['working_directory_respected'] = True
                self._print_success("Working directory context is respected!")
            else:
                test_result['evidence'] = "File handling inconsistent with cwd"
                self._print_warning("Working directory behavior unclear")
                if output1:
                    print(f"  From test-project: {output1[:100]}")
                else:
                    print(f"  From test-project: {result1.get('error', 'No output')}")
                if output2:
                    print(f"  From root: {output2[:100]}")
                else:
                    print(f"  From root: {result2.get('error', 'No output')}")

            self.results['tests'].append(test_result)
            print()

    def _test_slash_commands(self):
        """Test: /commands (exploratory - may not work)"""
        print(f"{Colors.BLUE}[Test 5]{Colors.END} Testing /commands (exploratory)...")
        
        slash_commands = ['/help', '/model']
        
        for cmd in slash_commands:
            result = self._run_gcli(cmd, cwd=self.test_dir)
            
            if result['success']:
                # Check if it looks like a command response vs regular chat
                output = result['output'].lower()
                if 'command' in output or 'help' in output or 'model' in output:
                    print(f"  {Colors.GREEN}✓{Colors.END} {cmd} may work - got relevant response")
                    self.results['slash_commands_work'] = True
                else:
                    print(f"  {Colors.YELLOW}?{Colors.END} {cmd} - unclear if command processed")
            else:
                print(f"  {Colors.RED}✗{Colors.END} {cmd} - failed or not recognized")
        
        if self.results['slash_commands_work'] is None:
            self.results['slash_commands_work'] = False
            print(f"\n  {Colors.YELLOW}Conclusion:{Colors.END} /commands likely don't work in -p mode")
            print("  This is acceptable - we'll implement them in Flask layer")
        
        print()
    
    def _test_stream_json(self):
        """Test: Stream-JSON with @file"""
        print(f"{Colors.BLUE}[Test 6]{Colors.END} Testing Stream-JSON with @file...")
        
        prompt = "Explain @src/main.py"
        
        result = self._run_gcli(prompt, cwd=self.test_dir, output_format='stream-json')
        
        if result['success']:
            # Try to parse JSON events
            lines = result['output'].strip().split('\n')
            json_events = []
            
            for line in lines:
                if line.strip():
                    try:
                        event = json.loads(line)
                        json_events.append(event)
                    except json.JSONDecodeError:
                        pass
            
            if json_events:
                self.results['stream_json_works'] = True
                self._print_success(f"Stream-JSON works! Found {len(json_events)} events")
                
                # Check event types
                event_types = set(e.get('type', 'unknown') for e in json_events)
                print(f"  Event types: {event_types}")
                
                # Check if @file content is in events
                full_text = ' '.join(e.get('text', '') for e in json_events if e.get('type') == 'text')
                if 'hello_world' in full_text.lower():
                    print(f"  {Colors.GREEN}✓{Colors.END} @file content present in stream")
            else:
                self._print_warning("Stream-JSON format not recognized")
                print(f"  Raw output: {result['output'][:200]}")
        else:
            self._print_error(f"Stream-JSON failed: {result.get('error')}")
        
        print()
    
    def _run_gcli(self, prompt: str, cwd: Path, output_format: str = None) -> dict:
        """
        Run GCLI with given prompt and options
        
        Returns:
            dict with 'success', 'output', 'error'
        """
        cmd = ['gemini']
        
        # Add output format if specified
        if output_format:
            cmd.extend(['-o', output_format])
        
        # Add prompt
        cmd.extend([self.flag, prompt])
        
        try:
            result = subprocess.run(
                cmd,
                cwd=str(cwd),
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'output': result.stdout.strip(),
                    'stderr': result.stderr.strip()
                }
            else:
                return {
                    'success': False,
                    'output': result.stdout.strip(),
                    'error': result.stderr.strip() or f"Exit code {result.returncode}"
                }
        
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Timeout (30s)'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_report(self):
        """Generate Phase 1 validation report"""
        print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
        print(f"{Colors.BOLD}Phase 1 Validation Report{Colors.END}")
        print(f"{Colors.BOLD}{'='*60}{Colors.END}\n")
        
        # Critical results
        critical_checks = [
            ("@file (single)", self.results['at_file_works']),
            ("@file (multiple)", self.results['at_file_multiple_works']),
            ("@directory", self.results['at_directory_works']),
            ("Working directory", self.results['working_directory_respected']),
        ]
        
        print(f"{Colors.BOLD}Critical Tests:{Colors.END}\n")
        for name, passed in critical_checks:
            status = f"{Colors.GREEN}✓ PASS{Colors.END}" if passed else f"{Colors.RED}✗ FAIL{Colors.END}"
            print(f"{status}  {name}")
        
        print(f"\n{Colors.BOLD}Optional Tests:{Colors.END}\n")
        slash_status = {
            True: f"{Colors.GREEN}✓ Works{Colors.END}",
            False: f"{Colors.YELLOW}✗ Doesn't work (OK){Colors.END}",
            None: f"{Colors.YELLOW}? Unknown{Colors.END}"
        }[self.results['slash_commands_work']]
        print(f"{slash_status}  /commands")
        
        stream_status = f"{Colors.GREEN}✓ Works{Colors.END}" if self.results['stream_json_works'] else f"{Colors.YELLOW}✗ Doesn't work{Colors.END}"
        print(f"{stream_status}  Stream-JSON")
        
        print()
        
        # Decision point
        print(f"{Colors.BOLD}Decision:{Colors.END}\n")
        
        if self.results['at_file_works']:
            print(f"{Colors.GREEN}✓ PROCEED TO PHASE 2{Colors.END}")
            print("  @file works - core functionality validated!")
            print(f"  Use: gemini {self.flag} 'prompt with @file'")
            
            if not self.results['stream_json_works']:
                print(f"\n{Colors.YELLOW}Note:{Colors.END} Stream-JSON not working")
                print("  Phase 5 will need alternative streaming approach")
            
        else:
            print(f"{Colors.RED}✗ BLOCKER - Cannot proceed{Colors.END}")
            print("  @file doesn't work in non-interactive mode")
            print("\n  Options:")
            print("    1. Manual file injection in Flask (less elegant)")
            print("    2. Use interactive mode with pexpect (more complex)")
            print("    3. Wait for GCLI update")
        
        print()
        
        # Architecture notes
        if self.results['at_file_works']:
            print(f"{Colors.BOLD}Architecture Decisions:{Colors.END}\n")
            print(f"  ✓ Use subprocess with cwd parameter")
            print(f"  ✓ Prompts can use @file syntax directly")
            print(f"  ✓ GCLI handles file resolution")
            
            if not self.results['slash_commands_work']:
                print(f"  ⚠ Implement /commands in Flask (intercept before GCLI)")
            
            if self.results['stream_json_works']:
                print(f"  ✓ Use -o stream-json for Phase 5")
            else:
                print(f"  ⚠ Phase 5: Parse plain text output (harder)")
        
        print()
        
        # Save results
        self._save_results()
    
    def _save_results(self):
        """Save results to JSON"""
        output_file = Path('docs/phase1_results.json')
        
        try:
            with open(output_file, 'w') as f:
                json.dump(self.results, f, indent=2)
            
            print(f"{Colors.GREEN}Results saved to:{Colors.END} {output_file}")
            
            # Update PHASE_VALIDATIONS.md
            self._update_validation_doc()
            
        except Exception as e:
            print(f"{Colors.RED}Could not save results:{Colors.END} {e}")
    
    def _update_validation_doc(self):
        """Update docs/PHASE_VALIDATIONS.md with Phase 1 results"""
        doc_file = Path('docs/PHASE_VALIDATIONS.md')
        
        if not doc_file.exists():
            return
        
        # Add Phase 1 section
        phase1_section = f"""

---

## Phase 1: Critical Validation - @file and /commands

**Date:** {time.strftime('%Y-%m-%d')}
**Status:** {'PASSED ✓' if self.results['at_file_works'] else 'FAILED ✗'}

### Test Results

- {'✓' if self.results['at_file_works'] else '✗'} @file single file
- {'✓' if self.results['at_file_multiple_works'] else '✗'} @file multiple files  
- {'✓' if self.results['at_directory_works'] else '✗'} @directory
- {'✓' if self.results['working_directory_respected'] else '✗'} Working directory context
- {'✓' if self.results.get('slash_commands_work') else '✗'} /commands
- {'✓' if self.results['stream_json_works'] else '✗'} Stream-JSON

### Critical Finding

**Do @file commands work in -p mode?** {'YES ✓' if self.results['at_file_works'] else 'NO ✗'}

### Decision

{'✓ PROCEED TO PHASE 2' if self.results['at_file_works'] else '✗ BLOCKED - See options in phase1_results.json'}

### Configuration for Next Phase

```python
# Subprocess invocation
subprocess.run(['gemini', '-p', prompt_with_at_files], cwd=working_dir, ...)
```
"""
        
        try:
            content = doc_file.read_text()
            
            # Append if Phase 1 section doesn't exist
            if 'Phase 1: Critical Validation' not in content:
                with open(doc_file, 'a') as f:
                    f.write(phase1_section)
                print(f"{Colors.GREEN}Updated:{Colors.END} docs/PHASE_VALIDATIONS.md")
        except Exception as e:
            print(f"{Colors.YELLOW}Could not update validation doc:{Colors.END} {e}")
    
    def _print_success(self, message: str):
        """Print success message"""
        print(f"{Colors.GREEN}✓{Colors.END} {message}")
    
    def _print_error(self, message: str):
        """Print error message"""
        print(f"{Colors.RED}✗{Colors.END} {message}")
    
    def _print_warning(self, message: str):
        """Print warning message"""
        print(f"{Colors.YELLOW}⚠{Colors.END} {message}")


def main():
    """Main entry point"""
    validator = Phase1Validator()
    results = validator.run_all_tests()
    
    print(f"\n{Colors.BOLD}Next Steps:{Colors.END}")
    
    if results['at_file_works']:
        print("  1. Review docs/phase1_results.json")
        print("  2. Proceed to Phase 2:")
        print("     python phase2_implement.py")
        print()
        sys.exit(0)
    else:
        print("  1. Review docs/phase1_results.json")
        print("  2. Decide on workaround approach")
        print("  3. Update implementation plan")
        print()
        sys.exit(1)


if __name__ == '__main__':
    main()