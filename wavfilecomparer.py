"""
Advanced WAV File Comparator - Windows GUI Application
Comprehensive binary, metadata, and audio content analysis
Version 3.0

Requirements:
pip install numpy
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import hashlib
import struct
import wave
import numpy as np
from datetime import datetime
from pathlib import Path
import threading
import json
import zlib

class WavComparator:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced WAV File Comparator v3.0")
        self.root.geometry("1200x850")
        self.root.minsize(900, 600)
        
        self.file1_path = tk.StringVar()
        self.file2_path = tk.StringVar()
        self.results_data = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the user interface"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(5, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Advanced WAV File Comparator", 
                                font=('Segoe UI', 16, 'bold'))
        title_label.grid(row=0, column=0, pady=(0, 10))
        
        # File selection frame
        file_frame = ttk.LabelFrame(main_frame, text="File Selection", padding="10")
        file_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)
        
        ttk.Label(file_frame, text="File 1:").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(file_frame, textvariable=self.file1_path).grid(
            row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(file_frame, text="Browse", 
                  command=lambda: self.browse_file(1)).grid(row=0, column=2)
        
        ttk.Label(file_frame, text="File 2:").grid(row=1, column=0, sticky=tk.W, pady=(5,0))
        ttk.Entry(file_frame, textvariable=self.file2_path).grid(
            row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=(5,0))
        ttk.Button(file_frame, text="Browse", 
                  command=lambda: self.browse_file(2)).grid(row=1, column=2, pady=(5,0))
        
        # Options frame
        options_frame = ttk.LabelFrame(main_frame, text="Analysis Options", padding="10")
        options_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.check_binary = tk.BooleanVar(value=True)
        self.check_metadata = tk.BooleanVar(value=True)
        self.check_audio = tk.BooleanVar(value=True)
        self.check_advanced = tk.BooleanVar(value=True)
        self.check_filesystem = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(options_frame, text="Binary/Hash Analysis", 
                       variable=self.check_binary).grid(row=0, column=0, sticky=tk.W, padx=5)
        ttk.Checkbutton(options_frame, text="Metadata/Chunk Analysis", 
                       variable=self.check_metadata).grid(row=0, column=1, sticky=tk.W, padx=5)
        ttk.Checkbutton(options_frame, text="Audio Content (Null Test)", 
                       variable=self.check_audio).grid(row=0, column=2, sticky=tk.W, padx=5)
        ttk.Checkbutton(options_frame, text="Advanced Signal Analysis", 
                       variable=self.check_advanced).grid(row=1, column=0, sticky=tk.W, padx=5)
        ttk.Checkbutton(options_frame, text="Filesystem Attributes", 
                       variable=self.check_filesystem).grid(row=1, column=1, sticky=tk.W, padx=5)
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, pady=(0, 10))
        
        self.compare_btn = ttk.Button(button_frame, text="🔍 Compare Files", 
                                      command=self.start_comparison, width=20)
        self.compare_btn.grid(row=0, column=0, padx=5)
        
        ttk.Button(button_frame, text="📄 Export Report", 
                  command=self.export_report, width=20).grid(row=0, column=1, padx=5)
        
        ttk.Button(button_frame, text="🗑️ Clear", 
                  command=self.clear_results, width=15).grid(row=0, column=2, padx=5)
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Results notebook
        results_frame = ttk.LabelFrame(main_frame, text="Comparison Results", padding="5")
        results_frame.grid(row=5, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        
        self.notebook = ttk.Notebook(results_frame)
        self.notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create tabs
        self.summary_text = scrolledtext.ScrolledText(self.notebook, wrap=tk.WORD, 
                                                       font=('Consolas', 10))
        self.notebook.add(self.summary_text, text="📋 Summary")
        
        self.detailed_text = scrolledtext.ScrolledText(self.notebook, wrap=tk.WORD, 
                                                        font=('Consolas', 9))
        self.notebook.add(self.detailed_text, text="📊 Detailed Analysis")
        
        self.diff_text = scrolledtext.ScrolledText(self.notebook, wrap=tk.WORD, 
                                                    font=('Consolas', 9))
        self.notebook.add(self.diff_text, text="⚠️ Differences")
        
        self.raw_text = scrolledtext.ScrolledText(self.notebook, wrap=tk.WORD, 
                                                   font=('Consolas', 8))
        self.notebook.add(self.raw_text, text="🔧 Raw JSON")
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=6, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
    def browse_file(self, file_num):
        """Open file browser"""
        filename = filedialog.askopenfilename(
            title=f"Select WAV File {file_num}",
            filetypes=[("WAV files", "*.wav"), ("All files", "*.*")]
        )
        if filename:
            if file_num == 1:
                self.file1_path.set(filename)
            else:
                self.file2_path.set(filename)
    
    def start_comparison(self):
        """Validate and start comparison in background thread"""
        if not self.file1_path.get() or not self.file2_path.get():
            messagebox.showwarning("Missing Files", "Please select both WAV files.")
            return
        
        if not os.path.exists(self.file1_path.get()):
            messagebox.showerror("Error", "File 1 does not exist.")
            return
        
        if not os.path.exists(self.file2_path.get()):
            messagebox.showerror("Error", "File 2 does not exist.")
            return
        
        self.compare_btn.config(state='disabled')
        self.progress.start(10)
        self.status_var.set("Analyzing files...")
        
        thread = threading.Thread(target=self.perform_comparison, daemon=True)
        thread.start()
    
    def perform_comparison(self):
        """Main comparison logic (runs in background thread)"""
        try:
            results = self.compare_files()
            self.root.after(0, self.display_results, results)
        except Exception as e:
            self.root.after(0, messagebox.showerror, "Analysis Error", str(e))
        finally:
            self.root.after(0, self.progress.stop)
            self.root.after(0, lambda: self.compare_btn.config(state='normal'))
            self.root.after(0, lambda: self.status_var.set("Complete"))
    
    def compare_files(self):
        """Perform all comparison analyses"""
        file1 = self.file1_path.get()
        file2 = self.file2_path.get()
        
        results = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'file1': file1,
            'file2': file2,
            'differences': [],
            'identical': True
        }
        
        if self.check_filesystem.get():
            results['filesystem'] = self.analyze_filesystem(file1, file2, results)
        
        if self.check_binary.get():
            results['binary'] = self.analyze_binary(file1, file2, results)
        
        if self.check_metadata.get():
            results['metadata'] = self.analyze_metadata(file1, file2, results)
        
        if self.check_audio.get():
            results['audio'] = self.analyze_audio_content(file1, file2, results)
        
        if self.check_advanced.get():
            results['advanced'] = self.analyze_advanced(file1, file2, results)
        
        return results
    
    def analyze_filesystem(self, file1, file2, results):
        """Filesystem metadata comparison"""
        stat1 = os.stat(file1)
        stat2 = os.stat(file2)
        path1 = Path(file1)
        path2 = Path(file2)
        
        fs_data = {
            'file1': {
                'name': path1.name,
                'size_bytes': stat1.st_size,
                'size_mb': round(stat1.st_size / (1024**2), 4),
                'created': datetime.fromtimestamp(stat1.st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
                'modified': datetime.fromtimestamp(stat1.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
            },
            'file2': {
                'name': path2.name,
                'size_bytes': stat2.st_size,
                'size_mb': round(stat2.st_size / (1024**2), 4),
                'created': datetime.fromtimestamp(stat2.st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
                'modified': datetime.fromtimestamp(stat2.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
            }
        }
        
        if path1.name != path2.name:
            results['differences'].append(f"Filename mismatch: '{path1.name}' vs '{path2.name}'")
            results['identical'] = False
        
        if stat1.st_size != stat2.st_size:
            results['differences'].append(f"File size: {stat1.st_size:,} vs {stat2.st_size:,} bytes")
            results['identical'] = False
        
        return fs_data
    
    def analyze_binary(self, file1, file2, results):
        """Complete binary analysis with multiple hash algorithms"""
        with open(file1, 'rb') as f:
            data1 = f.read()
        with open(file2, 'rb') as f:
            data2 = f.read()
        
        binary_data = {
            'file1': {
                'md5': hashlib.md5(data1).hexdigest(),
                'sha1': hashlib.sha1(data1).hexdigest(),
                'sha256': hashlib.sha256(data1).hexdigest(),
                'compression_ratio': self.get_compression_ratio(data1)
            },
            'file2': {
                'md5': hashlib.md5(data2).hexdigest(),
                'sha1': hashlib.sha1(data2).hexdigest(),
                'sha256': hashlib.sha256(data2).hexdigest(),
                'compression_ratio': self.get_compression_ratio(data2)
            },
            'byte_identical': data1 == data2
        }
        
        if not binary_data['byte_identical']:
            results['differences'].append("Binary: Files are NOT byte-for-byte identical")
            results['identical'] = False
            
            # Find first difference
            min_len = min(len(data1), len(data2))
            for i in range(min_len):
                if data1[i] != data2[i]:
                    binary_data['first_diff_byte'] = i
                    binary_data['first_diff_values'] = (data1[i], data2[i])
                    results['differences'].append(
                        f"First difference at byte {i}: 0x{data1[i]:02x} vs 0x{data2[i]:02x}")
                    break
            
            if len(data1) != len(data2):
                binary_data['size_diff'] = abs(len(data1) - len(data2))
                results['differences'].append(f"Size difference: {binary_data['size_diff']} bytes")
        
        return binary_data
    
    def get_compression_ratio(self, data):
        """Calculate zlib compression ratio"""
        compressed = zlib.compress(data, level=9)
        return round(len(data) / len(compressed), 3) if len(compressed) > 0 else 0
    
    def analyze_metadata(self, file1, file2, results):
        """Parse and compare WAV metadata chunks"""
        meta1 = self.parse_wav_chunks(file1)
        meta2 = self.parse_wav_chunks(file2)
        
        metadata = {'file1': meta1, 'file2': meta2}
        
        # Compare format chunks
        if meta1.get('fmt') and meta2.get('fmt'):
            fmt1 = meta1['fmt']
            fmt2 = meta2['fmt']
            
            for key in ['sample_rate', 'num_channels', 'bits_per_sample']:
                if fmt1.get(key) != fmt2.get(key):
                    results['differences'].append(
                        f"Format {key}: {fmt1.get(key)} vs {fmt2.get(key)}")
                    results['identical'] = False
        
        # Compare chunk structure
        chunks1 = set(meta1.get('all_chunks', []))
        chunks2 = set(meta2.get('all_chunks', []))
        
        if chunks1 != chunks2:
            only_1 = chunks1 - chunks2
            only_2 = chunks2 - chunks1
            if only_1:
                results['differences'].append(f"Chunks only in File 1: {', '.join(only_1)}")
            if only_2:
                results['differences'].append(f"Chunks only in File 2: {', '.join(only_2)}")
            results['identical'] = False
        
        return metadata
    
    def parse_wav_chunks(self, filepath):
        """Extract all WAV file chunks and metadata"""
        chunks_info = {'all_chunks': []}
        
        try:
            with open(filepath, 'rb') as f:
                riff = f.read(4)
                if riff != b'RIFF':
                    return {'error': 'Not a RIFF file'}
                
                file_size = struct.unpack('<I', f.read(4))[0]
                wave_id = f.read(4)
                
                if wave_id != b'WAVE':
                    return {'error': 'Not a WAVE file'}
                
                chunks_info['riff_size'] = file_size
                
                while f.tell() < file_size + 8:
                    chunk_id = f.read(4)
                    if len(chunk_id) < 4:
                        break
                    
                    chunk_size = struct.unpack('<I', f.read(4))[0]
                    chunk_name = chunk_id.decode('ascii', errors='ignore')
                    chunks_info['all_chunks'].append(chunk_name)
                    
                    if chunk_id == b'fmt ':
                        fmt_data = f.read(min(chunk_size, 16))
                        if len(fmt_data) >= 16:
                            chunks_info['fmt'] = {
                                'audio_format': struct.unpack('<H', fmt_data[0:2])[0],
                                'num_channels': struct.unpack('<H', fmt_data[2:4])[0],
                                'sample_rate': struct.unpack('<I', fmt_data[4:8])[0],
                                'byte_rate': struct.unpack('<I', fmt_data[8:12])[0],
                                'block_align': struct.unpack('<H', fmt_data[12:14])[0],
                                'bits_per_sample': struct.unpack('<H', fmt_data[14:16])[0]
                            }
                        if chunk_size > 16:
                            f.seek(chunk_size - 16, 1)
                    elif chunk_id == b'data':
                        chunks_info['data_size'] = chunk_size
                        chunks_info['data_offset'] = f.tell()
                        f.seek(chunk_size, 1)
                    else:
                        f.seek(chunk_size, 1)
                    
                    if chunk_size % 2:
                        f.read(1)
                        
        except Exception as e:
            chunks_info['error'] = str(e)
        
        return chunks_info
    
    def analyze_audio_content(self, file1, file2, results):
        """Audio sample comparison and null test"""
        try:
            with wave.open(file1, 'rb') as w1:
                params1 = w1.getparams()
                frames1 = w1.readframes(params1.nframes)
                dtype = np.int16 if params1.sampwidth == 2 else np.int32
                samples1 = np.frombuffer(frames1, dtype=dtype)
            
            with wave.open(file2, 'rb') as w2:
                params2 = w2.getparams()
                frames2 = w2.readframes(params2.nframes)
                dtype = np.int16 if params2.sampwidth == 2 else np.int32
                samples2 = np.frombuffer(frames2, dtype=dtype)
            
            audio_data = {
                'file1': {
                    'duration_sec': round(params1.nframes / params1.framerate, 3),
                    'num_samples': len(samples1),
                    'sample_rate': params1.framerate,
                    'channels': params1.nchannels,
                    'bit_depth': params1.sampwidth * 8
                },
                'file2': {
                    'duration_sec': round(params2.nframes / params2.framerate, 3),
                    'num_samples': len(samples2),
                    'sample_rate': params2.framerate,
                    'channels': params2.nchannels,
                    'bit_depth': params2.sampwidth * 8
                }
            }
            
            # Null test
            if len(samples1) == len(samples2):
                diff = samples1.astype(np.float64) - samples2.astype(np.float64)
                
                audio_data['null_test'] = {
                    'max_difference': int(np.max(np.abs(diff))),
                    'mean_difference': float(np.mean(np.abs(diff))),
                    'rms_difference': float(np.sqrt(np.mean(diff**2))),
                    'identical_percent': float(np.sum(diff == 0) / len(diff) * 100),
                    'samples_identical': bool(np.all(diff == 0))
                }
                
                if not audio_data['null_test']['samples_identical']:
                    results['differences'].append(
                        f"Audio: Samples differ (Max: {audio_data['null_test']['max_difference']}, "
                        f"RMS: {audio_data['null_test']['rms_difference']:.4f})")
                    results['identical'] = False
            else:
                results['differences'].append(
                    f"Audio: Different sample counts ({len(samples1)} vs {len(samples2)})")
                results['identical'] = False
            
            return audio_data
            
        except Exception as e:
            return {'error': str(e)}
    
    def analyze_advanced(self, file1, file2, results):
        """Advanced signal processing statistics"""
        try:
            with wave.open(file1, 'rb') as w1:
                params1 = w1.getparams()
                samples1 = np.frombuffer(w1.readframes(params1.nframes), dtype=np.int16)
            
            with wave.open(file2, 'rb') as w2:
                params2 = w2.getparams()
                samples2 = np.frombuffer(w2.readframes(params2.nframes), dtype=np.int16)
            
            advanced_data = {
                'file1': self.compute_audio_stats(samples1),
                'file2': self.compute_audio_stats(samples2)
            }
            
            # Cross-correlation
            if len(samples1) == len(samples2) and len(samples1) > 0:
                s1 = samples1.astype(np.float64)
                s2 = samples2.astype(np.float64)
                
                if np.std(s1) > 0 and np.std(s2) > 0:
                    corr = np.corrcoef(s1, s2)[0, 1]
                    advanced_data['correlation'] = float(corr)
                    
                    if corr < 0.9999:
                        results['differences'].append(f"Correlation: {corr:.6f} (not perfectly correlated)")
                        if corr < 0:
                            results['differences'].append("WARNING: Negative correlation (phase inverted)")
            
            return advanced_data
            
        except Exception as e:
            return {'error': str(e)}
    
    def compute_audio_stats(self, samples):
        """Calculate comprehensive audio statistics"""
        samples_float = samples.astype(np.float64)
        
        peak = int(np.max(np.abs(samples)))
        rms = float(np.sqrt(np.mean(samples_float**2)))
        
        max_val = 32768.0  # for 16-bit
        peak_dbfs = 20 * np.log10(peak / max_val) if peak > 0 else -np.inf
        rms_dbfs = 20 * np.log10(rms / max_val) if rms > 0 else -np.inf
        
        crest = peak / rms if rms > 0 else 0
        dc_offset = float(np.mean(samples_float))
        
        # Zero crossing rate
        signs = np.sign(samples_float)
        zero_crossings = np.sum(np.abs(np.diff(signs))) / 2
        zcr = zero_crossings / len(samples)
        
        return {
            'peak': peak,
            'peak_dbfs': float(peak_dbfs),
            'rms': float(rms),
            'rms_dbfs': float(rms_dbfs),
            'crest_factor': float(crest),
            'dc_offset': float(dc_offset),
            'zero_crossing_rate': float(zcr),
            'dynamic_range_db': float(peak_dbfs - rms_dbfs) if rms_dbfs != -np.inf else 0
        }
    
    def display_results(self, results):
        """Display formatted results in GUI"""
        self.clear_results()
        self.results_data = results
        
        # Summary tab
        summary = self.format_summary(results)
        self.summary_text.insert('1.0', summary)
        
        # Detailed tab
        detailed = self.format_detailed(results)
        self.detailed_text.insert('1.0', detailed)
        
        # Differences tab
        if results['differences']:
            diff_text = f"{'='*80}\nDIFFERENCES FOUND: {len(results['differences'])}\n{'='*80}\n\n"
            for i, diff in enumerate(results['differences'], 1):
                diff_text += f"{i:2d}. {diff}\n"
        else:
            diff_text = "✓ No differences found. Files are identical in all tested aspects."
        
        self.diff_text.insert('1.0', diff_text)
        
        # Raw JSON tab
        raw = json.dumps(results, indent=2, default=str)
        self.raw_text.insert('1.0', raw)
    
    def format_summary(self, results):
        """Format summary report"""
        lines = []
        lines.append("=" * 80)
        lines.append("ADVANCED WAV FILE COMPARISON REPORT")
        lines.append(f"Generated: {results['timestamp']}")
        lines.append("=" * 80)
        lines.append(f"\nFile 1: {Path(results['file1']).name}")
        lines.append(f"        {results['file1']}")
        lines.append(f"\nFile 2: {Path(results['file2']).name}")
        lines.append(f"        {results['file2']}")
        lines.append("\n" + "=" * 80)
        
        if results['identical']:
            lines.append("\n✓✓✓ FILES ARE IDENTICAL ✓✓✓")
            lines.append("All analyzed aspects match perfectly.")
        else:
            lines.append("\n⚠️  FILES ARE DIFFERENT  ⚠️")
            lines.append(f"{len(results['differences'])} difference(s) detected.")
        
        lines.append("\n" + "=" * 80)
        lines.append("QUICK SUMMARY:")
        lines.append("=" * 80)
        
        # Binary
        if 'binary' in results:
            if results['binary'].get('byte_identical'):
                lines.append("✓ Binary: IDENTICAL (byte-for-byte match)")
            else:
                lines.append("✗ Binary: DIFFERENT")
                if 'first_diff_byte' in results['binary']:
                    lines.append(f"  First diff at byte {results['binary']['first_diff_byte']}")
        
        # Audio
        if 'audio' in results and 'null_test' in results['audio']:
            null = results['audio']['null_test']
            if null.get('samples_identical'):
                lines.append("✓ Audio: IDENTICAL (perfect null test)")
            else:
                lines.append(f"✗ Audio: DIFFERENT (RMS diff: {null.get('rms_difference', 'N/A')})")
        
        # Metadata
        if 'metadata' in results:
            m1 = results['metadata'].get('file1', {})
            m2 = results['metadata'].get('file2', {})
            if m1.get('fmt') == m2.get('fmt'):
                lines.append("✓ Format: IDENTICAL")
            else:
                lines.append("✗ Format: DIFFERENT")
        
        # Filesystem
        if 'filesystem' in results:
            fs1 = results['filesystem']['file1']
            fs2 = results['filesystem']['file2']
            lines.append(f"\n📁 File Sizes: {fs1['size_mb']} MB vs {fs2['size_mb']} MB")
            if fs1['name'] != fs2['name']:
                lines.append(f"📝 Filenames differ: '{fs1['name']}' vs '{fs2['name']}'")
        
        return '\n'.join(lines)
    
    def format_detailed(self, results):
        """Format detailed analysis"""
        lines = []
        
        # Filesystem
        if 'filesystem' in results:
            lines.append("=" * 80)
            lines.append("FILESYSTEM ATTRIBUTES")
            lines.append("=" * 80)
            for file_key in ['file1', 'file2']:
                lines.append(f"\n{file_key.upper()}:")
                for key, val in results['filesystem'][file_key].items():
                    lines.append(f"  {key:20s}: {val}")
        
        # Binary
        if 'binary' in results:
            lines.append("\n" + "=" * 80)
            lines.append("BINARY ANALYSIS")
            lines.append("=" * 80)
            binary = results['binary']
            lines.append(f"\nByte-identical: {binary['byte_identical']}")
            
            for file_key in ['file1', 'file2']:
                lines.append(f"\n{file_key.upper()} Hashes:")
                lines.append(f"  MD5    : {binary[file_key]['md5']}")
                lines.append(f"  SHA1   : {binary[file_key]['sha1']}")
                lines.append(f"  SHA256 : {binary[file_key]['sha256']}")
                lines.append(f"  Compress: {binary[file_key]['compression_ratio']}:1")
        
        # Metadata
        if 'metadata' in results:
            lines.append("\n" + "=" * 80)
            lines.append("METADATA / CHUNK STRUCTURE")
            lines.append("=" * 80)
            
            for file_key in ['file1', 'file2']:
                meta = results['metadata'][file_key]
                lines.append(f"\n{file_key.upper()}:")
                
                if 'error' in meta:
                    lines.append(f"  Error: {meta['error']}")
                else:
                    lines.append(f"  Chunks found: {', '.join(meta.get('all_chunks', []))}")
                    
                    if 'fmt' in meta:
                        lines.append("  Format chunk:")
                        for key, val in meta['fmt'].items():
                            lines.append(f"    {key:20s}: {val}")
                    
                    if 'data_size' in meta:
                        lines.append(f"  Data chunk size: {meta['data_size']:,} bytes")
        
        # Audio content
        if 'audio' in results:
            lines.append("\n" + "=" * 80)
            lines.append("AUDIO CONTENT ANALYSIS")
            lines.append("=" * 80)
            
            if 'error' in results['audio']:
                lines.append(f"\nError: {results['audio']['error']}")
            else:
                for file_key in ['file1', 'file2']:
                    if file_key in results['audio']:
                        audio = results['audio'][file_key]
                        lines.append(f"\n{file_key.upper()}:")
                        lines.append(f"  Duration      : {audio['duration_sec']} seconds")
                        lines.append(f"  Sample Rate   : {audio['sample_rate']:,} Hz")
                        lines.append(f"  Channels      : {audio['channels']}")
                        lines.append(f"  Bit Depth     : {audio['bit_depth']} bits")
                        lines.append(f"  Total Samples : {audio['num_samples']:,}")
                
                if 'null_test' in results['audio']:
                    null = results['audio']['null_test']
                    lines.append("\n  NULL TEST RESULTS:")
                    if 'error' in null:
                        lines.append(f"    Error: {null['error']}")
                    else:
                        lines.append(f"    Samples Identical : {null['samples_identical']}")
                        lines.append(f"    Max Difference    : {null['max_difference']}")
                        lines.append(f"    Mean Difference   : {null['mean_difference']:.4f}")
                        lines.append(f"    RMS Difference    : {null['rms_difference']:.4f}")
                        lines.append(f"    Identical %       : {null['identical_percent']:.2f}%")
        
        # Advanced analysis
        if 'advanced' in results:
            lines.append("\n" + "=" * 80)
            lines.append("ADVANCED SIGNAL ANALYSIS")
            lines.append("=" * 80)
            
            if 'error' in results['advanced']:
                lines.append(f"\nError: {results['advanced']['error']}")
            else:
                for file_key in ['file1', 'file2']:
                    if file_key in results['advanced']:
                        stats = results['advanced'][file_key]
                        lines.append(f"\n{file_key.upper()} Statistics:")
                        lines.append(f"  Peak Level        : {stats['peak']:,} ({stats['peak_dbfs']:.2f} dBFS)")
                        lines.append(f"  RMS Level         : {stats['rms']:.2f} ({stats['rms_dbfs']:.2f} dBFS)")
                        lines.append(f"  Crest Factor      : {stats['crest_factor']:.2f}")
                        lines.append(f"  DC Offset         : {stats['dc_offset']:.2f}")
                        lines.append(f"  Dynamic Range     : {stats['dynamic_range_db']:.2f} dB")
                        lines.append(f"  Zero Crossing Rate: {stats['zero_crossing_rate']:.6f}")
                
                if 'correlation' in results['advanced']:
                    lines.append(f"\n  CORRELATION COEFFICIENT: {results['advanced']['correlation']:.6f}")
                    corr = results['advanced']['correlation']
                    if corr > 0.9999:
                        lines.append("    → Nearly perfect correlation")
                    elif corr > 0.99:
                        lines.append("    → Very high correlation")
                    elif corr > 0.9:
                        lines.append("    → Strong correlation")
                    elif corr > 0:
                        lines.append("    → Weak positive correlation")
                    elif corr < 0:
                        lines.append("    → NEGATIVE correlation (phase inverted)")
        
        return '\n'.join(lines)
    
    def clear_results(self):
        """Clear all result text areas"""
        self.summary_text.delete('1.0', tk.END)
        self.detailed_text.delete('1.0', tk.END)
        self.diff_text.delete('1.0', tk.END)
        self.raw_text.delete('1.0', tk.END)
        self.results_data = None
        self.status_var.set("Ready")
    
    def export_report(self):
        """Export analysis results to text file"""
        if not self.results_data:
            messagebox.showwarning("No Data", "Please run a comparison first.")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Save Report As",
            defaultextension=".txt",
            filetypes=[
                ("Text files", "*.txt"),
                ("JSON files", "*.json"),
                ("All files", "*.*")
            ]
        )
        
        if filename:
            try:
                if filename.endswith('.json'):
                    with open(filename, 'w') as f:
                        json.dump(self.results_data, f, indent=2, default=str)
                else:
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(self.format_summary(self.results_data))
                        f.write("\n\n")
                        f.write(self.format_detailed(self.results_data))
                        f.write("\n\n")
                        f.write("=" * 80)
                        f.write("\nDIFFERENCES LIST\n")
                        f.write("=" * 80 + "\n")
                        for i, diff in enumerate(self.results_data['differences'], 1):
                            f.write(f"{i}. {diff}\n")
                
                messagebox.showinfo("Success", f"Report exported to:\n{filename}")
                self.status_var.set(f"Report exported: {Path(filename).name}")
                
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export report:\n{str(e)}")


def main():
    """Application entry point"""
    root = tk.Tk()
    app = WavComparator(root)
    root.mainloop()


if __name__ == "__main__":
    main()
