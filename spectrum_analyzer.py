"""
Spectrum Analysis Module for Ocean View Spectrometer
Identifies food dyes based on transmission curve inflection points
FINAL VERSION - Finds where transmission starts rising
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import time
import os
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


def identify_dye(inflection_wavelength):
    """
    Identify dye based on where transmission curve starts rising.
    
    Based on empirical data from your setup:
    - Red 40: Transmission rises around 580 nm
    - Yellow 6: Transmission rises around 480-500 nm  
    - Yellow 5: Transmission rises around 500-520 nm (with feature at 680nm)
    - Blue 1: Transmission rises around 450-500 nm (with feature at 680nm)
    """
    
    # These ranges are where transmission STARTS to rise significantly
    if 560 <= inflection_wavelength <= 620:
        return "Red 40", "Red"
    elif 510 <= inflection_wavelength <= 559:
        return "Yellow 5", "Yellow"
    elif 470 <= inflection_wavelength <= 509:
        return "Yellow 6", "Yellow-Orange"
    elif 440 <= inflection_wavelength <= 469:
        return "Blue 1", "Blue"
    else:
        # Default to closest
        distances = {
            "Red 40": abs(inflection_wavelength - 590),
            "Yellow 5": abs(inflection_wavelength - 515),
            "Yellow 6": abs(inflection_wavelength - 490),
            "Blue 1": abs(inflection_wavelength - 455)
        }
        closest = min(distances, key=distances.get)
        return f"{closest} (closest match)", {"Red 40": "Red", "Yellow 5": "Yellow", 
                                               "Yellow 6": "Yellow-Orange", "Blue 1": "Blue"}[closest]


def analyze_spectrum(file_path, show_plot=False):
    """
    Analyze transmission spectrum by finding the inflection point
    where transmission starts rising significantly.
    """
    try:
        # Read data
        df = pd.read_csv(file_path, sep=r'\s+', skiprows=14, header=None, 
                         names=['Wavelength', 'Intensity'])
        
        wavelength = df['Wavelength'].values
        intensity = df['Intensity'].values
        
        # Focus on visible spectrum (400-650 nm) - excludes edge effects
        vis_mask = (wavelength >= 400) & (wavelength <= 650)
        vis_wl = wavelength[vis_mask]
        vis_int = intensity[vis_mask]
        
        # Smooth the data
        window = 5
        smoothed = np.convolve(vis_int, np.ones(window)/window, mode='same')
        
        # Calculate first derivative (rate of change)
        derivative = np.gradient(smoothed, vis_wl)
        
        # Find the point of maximum rate of increase (steepest rise)
        max_derivative_idx = np.argmax(derivative)
        inflection_wavelength = vis_wl[max_derivative_idx]
        inflection_intensity = smoothed[max_derivative_idx]
        max_derivative_value = derivative[max_derivative_idx]
        
        # Identify the dye
        dye_name, color_name = identify_dye(inflection_wavelength)
        
        # Print results
        print("\n" + "="*70)
        print("TRANSMISSION SPECTRUM ANALYSIS")
        print("="*70)
        print(f"File: {os.path.basename(file_path)}")
        print(f"Transmission Rise Point: {inflection_wavelength:.2f} nm")
        print(f"Intensity at inflection: {inflection_intensity:.2f}")
        print(f"Rate of rise: {max_derivative_value:.2f}")
        print(f"Identified Dye: {dye_name}")
        print(f"Color: {color_name}")
        print("="*70 + "\n")
        
        if show_plot:
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
            
            # Top plot: Transmission spectrum
            ax1.plot(vis_wl, vis_int, 'b-', alpha=0.3, linewidth=1, label='Raw Data')
            ax1.plot(vis_wl, smoothed, 'b-', linewidth=2, label='Smoothed Data')
            ax1.plot(inflection_wavelength, inflection_intensity, 'ro', markersize=12, 
                    label=f'Inflection Point: {inflection_wavelength:.1f} nm', zorder=5)
            ax1.axvline(x=inflection_wavelength, color='r', linestyle='--', alpha=0.7, linewidth=2)
            ax1.set_xlabel("Wavelength (nm)", fontsize=12, fontweight='bold')
            ax1.set_ylabel("Transmission Intensity", fontsize=12, fontweight='bold')
            ax1.set_title(f"Transmission Spectrum: {dye_name} ({color_name})", fontsize=14, fontweight='bold')
            ax1.grid(True, alpha=0.3)
            ax1.legend(loc='best')
            
            # Bottom plot: Derivative (rate of change)
            ax2.plot(vis_wl, derivative, 'g-', linewidth=2, label='Rate of Change (Derivative)')
            ax2.plot(inflection_wavelength, max_derivative_value, 'ro', markersize=12, 
                    label=f'Maximum Rise Rate: {inflection_wavelength:.1f} nm', zorder=5)
            ax2.axvline(x=inflection_wavelength, color='r', linestyle='--', alpha=0.7, linewidth=2)
            ax2.axhline(y=0, color='k', linestyle='-', alpha=0.3)
            ax2.set_xlabel("Wavelength (nm)", fontsize=12, fontweight='bold')
            ax2.set_ylabel("Rate of Transmission Increase", fontsize=12, fontweight='bold')
            ax2.set_title("Derivative Analysis", fontsize=14, fontweight='bold')
            ax2.grid(True, alpha=0.3)
            ax2.legend(loc='best')
            
            plt.tight_layout()
            plt.show()
        
        return inflection_wavelength, inflection_intensity, dye_name, color_name
    
    except Exception as e:
        print(f"❌ Error analyzing {file_path}: {e}")
        import traceback
        traceback.print_exc()
        return None, None, "Error", "Error"


class SpectrumFileHandler(FileSystemEventHandler):
    """
    Monitors folder for new spectrum files and automatically analyzes them.
    """
    def on_created(self, event):
        if event.is_directory:
            return
        
        if event.src_path.endswith('.txt'):
            print(f"\n🔍 NEW FILE DETECTED: {os.path.basename(event.src_path)}")
            time.sleep(0.5)
            
            try:
                analyze_spectrum(event.src_path, show_plot=False)
            except Exception as e:
                print(f"❌ Error analyzing {event.src_path}: {e}")


def start_monitoring(folder_path):
    """
    Start monitoring a folder for new spectrum files.
    
    Usage:
        start_monitoring(r"C:/Users/Blab2/Desktop/Project/oceanview_data")
    """
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        print(f"Created folder: {folder_path}")
    
    event_handler = SpectrumFileHandler()
    observer = Observer()
    observer.schedule(event_handler, folder_path, recursive=False)
    observer.start()
    
    print("\n" + "="*70)
    print("🎨 DYE ANALYSIS SYSTEM - MONITORING ACTIVE 🎨")
    print("="*70)
    print(f"📁 Watching folder: {folder_path}")
    print(f"🔬 Monitoring for: Yellow 5, Yellow 6, Red 40, Blue 1")
    print(f"⏸️  Press Ctrl+C to stop monitoring...")
    print("="*70 + "\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n\n⏹️  Monitoring stopped.\n")
    observer.join()


def test_file(file_path):
    """
    Test analysis on a single file with plot.
    
    Usage:
        test_file(r"C:/Users/Blab2/Desktop/Project/oceanview_data/your_file.txt")
    """
    print(f"\n📊 Testing file: {file_path}\n")
    result = analyze_spectrum(file_path, show_plot=True)
    return result


if __name__ == "__main__":
    folder = r"C:\Users\Blab2\Desktop\Project\oceanview_data"
    start_monitoring(folder)