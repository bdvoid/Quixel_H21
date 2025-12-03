# Quixel Megascans Plugin for Houdini 21

Modified Megascans LiveLink plugin for SideFX Houdini 21, providing enhanced USD/Solaris workflow support with MaterialX and improved renderer compatibility.

## Overview

This is a modified version of the official Quixel Megascans Houdini plugin (v4.6) that enables:
- **USD Component Builder workflow** for asset imports in Solaris
- **Variant management** for LODs and material variations
- **MaterialX (mtlx)** support for Karma and Redshift
- **Enhanced renderer support**: Arnold, Karma, Mantra, Octane, Redshift, Renderman
- **Improved viewport visualization** for Redshift materials

## Installation

### 1. Download Megascans Plugin

1. Open **Quixel Bridge**
2. Go to **Edit > Manage Plugins > Houdini**
3. Download **Houdini 4.6** plugin

### 2. Configure Houdini Package

Create or modify the package JSON file:

**Location**: `Documents/houdini21.0/packages/Quixel.json`

**Important**: Update the path to match your installation directory.

### 3. Install Modified Files

**Clone this repository**
into the Quixel Bridge plugin folder.

```
git clone https://github.com/bdvoid/Quixel_H21.git
```
### USD/Solaris Workflow

1. Create a **LOP network** in Houdini
2. Export asset from Bridge with **USD** option enabled
3. Plugin creates **Component Builder** nodes with:
   - LOD variants (High, Medium, Low)
   - Material variants (if available)
   - Proper USD hierarchy

## Contributing

Feel free to submit issues and enhancement requests!

## Changelog
### Version 1.0 (Houdini 21 Compatible)
- Updated for Houdini 21 compatibility
- Enhanced USD/Solaris workflow
- MaterialX support for Karma and Redshift
- Improved Component Builder integration
- Updated Redshift to Standard Shader
- Viewport material preview improvements
