# Ocean Simulation

A Python program that renders a realistic ocean surface using spectral wave synthesis, with interactive parameter controls that trigger re-renders. The project demonstrates a pipeline of interconnected graphics techniques.

## Setup

```bash
pip install -r requirements.txt
```

## Running

```bash
python ocean-sim
```

### Controls

The ocean animates in real time, and every change in the control panel shows up immediately.

- **Drag** the ocean to orbit the camera, **scroll** to zoom
- **Space** pauses and resumes; the **Time** slider scrubs through the loop
- **Save Image** and **Render Animation** render in the background at the **Export grid** resolution, saving to `images/` and `videos/`

The live view simulates a smaller grid (**Live grid**, 256 by default) cut from the same wave spectrum, so it shows the same ocean as the exports with less fine detail.