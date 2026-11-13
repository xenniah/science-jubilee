"""
Diagnostic tool to find actual absorption wavelengths for your dyes
Run this on each of your 4 reference samples to find their TRUE absorption ranges
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def find_absorption_peaks(file_path, dye_name):
    """
    Scans entire visible spectrum and finds strongest absorption wavelengths.
    
    Parameters:
    - file_path: Path to spectrum file
    - dye_name: Name of the dye (for labeling)
    """
    # Read data
    df = pd.read_csv(file_path, sep=r'\s+', skiprows=14, header=None, 
                     names=['Wavelength', 'Intensity'])
    
    wavelength = df['Wavelength'].values
    intensity = df['Intensity'].values
    
    # Focus on visible spectrum (380-700 nm)
    visible_mask = (wavelength >= 380) & (wavelength <= 700)
    vis_wl = wavelength[visible_mask]
    vis_int = intensity[visible_mask]
    
    # Smooth the data to reduce noise (moving average)
    window = 5
    smoothed = np.convolve(vis_int, np.ones(window)/window, mode='same')
    
    # Calculate derivative to find local minima
    derivative = np.diff(smoothed)
    
    # Find points where derivative changes from negative to positive (local minima)
    minima_indices = []
    for i in range(1, len(derivative)-1):
        if derivative[i-1] < 0 and derivative[i] > 0:
            minima_indices.append(i)
    
    # Get the 3 strongest absorption peaks (lowest transmission)
    if len(vis_int) > 0:
        sorted_indices = np.argsort(smoothed)[:10]  # Get 10 lowest points
        
        print(f"\n{'='*70}")
        print(f"ABSORPTION ANALYSIS: {dye_name}")
        print(f"{'='*70}")
        print(f"Top 10 absorption wavelengths (lowest transmission):")
        print(f"{'Rank':<6} {'Wavelength (nm)':<18} {'Intensity':<15} {'% of max'}")
        print(f"{'-'*70}")
        
        max_intensity = np.max(smoothed)
        for rank, idx in enumerate(sorted_indices, 1):
            wl = vis_wl[idx]
            inten = smoothed[idx]
            percent = (inten / max_intensity) * 100
            print(f"{rank:<6} {wl:<18.2f} {inten:<15.2f} {percent:.1f}%")
        
        # Find the primary absorption peak (lowest point)
        primary_idx = sorted_indices[0]
        primary_wl = vis_wl[primary_idx]
        
        print(f"\n{'='*70}")
        print(f"PRIMARY ABSORPTION: {primary_wl:.2f} nm")
        print(f"{'='*70}\n")
        
        # Plot the spectrum
        plt.figure(figsize=(14, 7))
        plt.plot(vis_wl, vis_int, 'b-', alpha=0.3, linewidth=1, label='Raw Data')
        plt.plot(vis_wl, smoothed, 'b-', linewidth=2, label='Smoothed Data')
        
        # Highlight top 3 absorption peaks
        for i, idx in enumerate(sorted_indices[:3]):
            color = ['red', 'orange', 'yellow'][i]
            label = ['Primary', 'Secondary', 'Tertiary'][i]
            plt.plot(vis_wl[idx], smoothed[idx], 'o', color=color, markersize=12, 
                    label=f'{label}: {vis_wl[idx]:.1f} nm', zorder=5)
        
        plt.xlabel("Wavelength (nm)", fontsize=13, fontweight='bold')
        plt.ylabel("Transmission Intensity", fontsize=13, fontweight='bold')
        plt.title(f"Absorption Spectrum Analysis: {dye_name}", fontsize=15, fontweight='bold')
        plt.grid(True, alpha=0.3)
        plt.legend(loc='best', fontsize=11)
        plt.xlim(380, 700)
        plt.tight_layout()
        plt.show()
        
        return primary_wl
    
    return None


# Run this for each of your 4 dyes
if __name__ == "__main__":
    print("\n" + "="*70)
    print("DYE ABSORPTION WAVELENGTH FINDER")
    print("="*70)
    print("\nRun this on each reference sample to find actual absorption ranges\n")
    
    # Replace these paths with your actual file paths
    samples = {
        "Red 40": r"C:\Users\Blab2\Desktop\Project\oceanview_data\QEP075821__1__10-58-49-949.txt",
        "Yellow 5": r"C:\Users\Blab2\Desktop\Project\oceanview_data\QEP075821__2__11-02-16-320.txt",
        "Yellow 6": r"C:\Users\Blab2\Desktop\Project\oceanview_data\QEP075821__3__11-04-17-157.txt",
        "Blue 1": r"C:\Users\Blab2\Desktop\Project\oceanview_data\QEP075821__4__11-05-52-018.txt"
    }
    
    absorption_wavelengths = {}
    
    for dye_name, file_path in samples.items():
        try:
            primary_wl = find_absorption_peaks(file_path, dye_name)
            absorption_wavelengths[dye_name] = primary_wl
        except Exception as e:
            print(f"Error analyzing {dye_name}: {e}")
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY - ACTUAL ABSORPTION WAVELENGTHS")
    print("="*70)
    for dye, wl in absorption_wavelengths.items():
        if wl:
            print(f"{dye:<15}: {wl:.2f} nm")
    print("="*70)
    print("\nUse these wavelengths to update the dye ranges in spectrum_analyzer.py!")