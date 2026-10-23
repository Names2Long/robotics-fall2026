"""Portable evaluation tables and figures regenerated from saved predictions."""
import csv
import io
import json


def csv_data(rows, columns=None):
    output = io.StringIO()
    if rows or columns:
        writer = csv.DictWriter(output,fieldnames=columns or list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return output.getvalue().encode('utf-8')


def artifacts(evidence, result):
    if evidence.get('method') != 'learned': return
    rows = evidence['representations']['rows']
    yield 'classification_predictions.csv',csv_data([
        {k:r[k] for k in ('image_id','condition','expected','cup_score','classifier_ms')} |
        {'top5':json.dumps(r['top5'])} for r in rows])
    yield 'segmentation_metrics.csv',csv_data(result['segmentation'])
    points = result['detection_pr']['points']
    yield 'detection_pr.csv',csv_data(points,['score','precision','recall'])
    path = ' '.join(f"{50+400*p['recall']:.2f},{250-200*p['precision']:.2f}" for p in points)
    figure = f'''<svg xmlns="http://www.w3.org/2000/svg" width="520" height="310" viewBox="0 0 520 310">
<rect width="520" height="310" fill="white"/>
<path d="M50 40 V250 H470" fill="none" stroke="black"/>
<polyline points="{path}" fill="none" stroke="#1769aa" stroke-width="2"/>
<g font-family="sans-serif" font-size="14" fill="black">
<text x="55" y="25">Cup box precision–recall at IoU 0.50</text>
<text x="220" y="295">Recall (0 to 1)</text>
<text x="5" y="45">1</text><text x="25" y="250">0</text>
<text x="50" y="270">0</text><text x="450" y="270">1</text>
<text x="8" y="145" transform="rotate(-90 8 145)">Precision</text></g></svg>'''
    yield 'detection_pr.svg',figure.encode('utf-8')
    c = result['classification']
    figure = f'''<svg xmlns="http://www.w3.org/2000/svg" width="500" height="240">
<rect width="500" height="240" fill="white"/><g font-family="sans-serif" font-size="15" fill="black">
<text x="20" y="25">Cup-presence classification confusion matrix</text>
<text x="175" y="65">Predicted absent</text><text x="330" y="65">Predicted present</text>
<text x="20" y="115">Actual absent</text><text x="220" y="115">TN {c['tn']}</text><text x="370" y="115">FP {c['fp']}</text>
<text x="20" y="175">Actual present</text><text x="220" y="175">FN {c['fn']}</text><text x="370" y="175">TP {c['tp']}</text>
</g></svg>'''
    yield 'classification_confusion.svg',figure.encode('utf-8')
    summary = f'''# Visual evaluation

Shared images: {len(rows)}. Cup detection threshold: {evidence['selected_threshold']}.
NMS overlap: {evidence['nms_iou']}. Classification cup-score threshold: {evidence['classification_threshold']}.
Foreground threshold: {evidence['segmentation_threshold']}.

Cup AP50: {result['detection_pr']['ap50']}.
Classification accuracy: {c['accuracy']}, precision: {c['precision']}, recall: {c['recall']}.

Classification maps the ImageNet cup and coffee mug scores to a binary rule. The segmenter predicts class-agnostic salient foreground, evaluated against the desired cup region. These are different output tasks.

Pixel annotations are approximate manually traced visible-cup silhouettes. Independent photos have no pixel labels and are excluded from mask scores. Both-empty masks score 1. Inspect target-present and absent rows separately.

AP50 uses one cup class at IoU 0.50, with a 0.001 proposal score floor. It is not multiclass or multi-IoU COCO mAP. Timings exclude loading, transport and action. See the mission explanation for the student's conclusions.
'''
    yield 'evaluation_summary.md',summary.encode('utf-8')
