from typing import Optional
import numpy as np
import cv2
import vqpy


@vqpy.vqpy_func_logger(['image'], ['major_color_rgb'], [], required_length=1)
def get_image_color(obj, image: Optional[np.ndarray]) -> str:
    import webcolors
    from colordetect import ColorDetect

    class BindedColorDetect(ColorDetect):
        def _find_unique_colors(self, cluster, centroids) -> dict:
            labels = np.arange(0, len(np.unique(cluster.labels_)) + 1)
            (hist, _) = np.histogram(cluster.labels_, bins=labels)
            hist = hist.astype("float")
            hist /= hist.sum()

            # iterate through each cluster's color and percentage
            colors = sorted(
                [(percent * 100, color)
                 for (percent, color) in zip(hist, centroids)],
                key=lambda x: (x[0], x[1].tolist())
            )

            for (percent, color) in colors:
                color.astype("uint8").tolist()
            return dict(colors)

    if image is None:
        return [None]
    ratio = max(32 / image.shape[0], 32 / image.shape[1])
    if ratio < 1:
        size = (int(image.shape[0] * ratio + 0.5),
                int(image.shape[1] * ratio + 0.5))
        image = cv2.resize(image, size, interpolation=cv2.INTER_LINEAR)
    # print(f'Image shape = {image.shape}')
    detector = BindedColorDetect(image)
    result = detector.get_color_count()
    bestrgb, bestp = None, 0
    for color, percent in result.items():
        rgb = webcolors.name_to_rgb(color)
        if max(*rgb) - min(*rgb) <= 15:
            percent /= 5
        if percent > bestp:
            bestrgb, bestp = rgb, percent
    # if 'red' in bestcolor:
    # print(result)
    # print(bestrgb, bestp)
    return [bestrgb]
