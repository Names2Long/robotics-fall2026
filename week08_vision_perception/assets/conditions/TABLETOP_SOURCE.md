# Multi-object tabletop scene

`tabletop.jpg` is the unmodified original **Laptop and a mug**, Ryan Riggins, February 24, 2017.

Source and CC0 license record: https://commons.wikimedia.org/wiki/File:Laptop_and_a_mug_(Unsplash).jpg

Original: https://upload.wikimedia.org/wikipedia/commons/0/0b/Laptop_and_a_mug_%28Unsplash%29.jpg

The photograph contains a mug, laptop, separate keyboard and trackpad. The teaching scenario is an assistive robot locating a mug while leaving desk equipment alone. This is not a photograph of a robot, evidence of safe grasping or a calibrated robot camera.

The runtime makes a 480 by 320 teaching image. Its approximate hand-traced visible-mug polygon and handle hole are recorded in `tabletop_annotation.json`, independently of either model. The mug is clipped at the top of the source photograph. Its reference box encloses only the visible extent. Transformed images and mask/box derivatives retain the CC0 dedication. Transformations are controlled image tests, not additional physical viewpoints.

The older coffee photograph and annotations remain available for historical evidence but are no longer the source scene. The two independent photographs retain their original source credits in README.md.
