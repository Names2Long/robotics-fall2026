# mission_1

## diagnosis
During practice, I lowered the minimum circularity from 0.60 to 0.10 while keeping the other settings unchanged. The mask stayed the same because circularity filters the contours after the mask is created. Before the change, candidate 0 was rejected because its circularity was 0.1355, below 0.60. After lowering the threshold, it became eligible. Its area of 107,338.5 pixels^2 also exceeded the minimum area of 3,193. A green box appeared around almost the entire image rather than isolating the mug. This shows that allowing less circular regions can produce a detection without correctly locating the target. A different cup could fail the color thresholds, while a background with matching colors could be selected instead.

## limitations
I changed the minimum circularity from 0.60 to 0.10, keeping all other settings the same. The mask did not change, but a green box appeared around almost the entire image. The contour’s circularity was 0.1355, so it failed the original threshold but passed the lower one. The box still did not isolate the mug. This shows that passing the shape filter does not mean the detector found a cup. A differently colored cup could be missed, and a background matching the color rule could be selected instead.
