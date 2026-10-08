from lab.session import response, set_response


def text_response(st, key, label, height=110):
    widget = f"field.{key}"
    if widget not in st.session_state:
        st.session_state[widget] = str(response(st, key, ""))
    value = st.text_area(label, height=height, key=widget)
    set_response(st, key, value)
    return value


def render_check(st, check):
    st.dataframe(
        [{"Requirement": item.label, "Actual": str(item.actual), "Expected": str(item.expected),
          "Status": "Pass" if item.passed else "Not yet"} for item in check.requirements],
        hide_index=True, width="stretch",
    )
    (st.success if check.passed else st.warning)(
        check.summary if check.passed else "The mission is not complete yet. Review the requirements above."
    )


def show_map(st, image_item, caption, width=620):
    if image_item is None:
        return
    from analysis.map_metrics import read_pgm_bytes
    import numpy as np

    try:
        width, height, maximum, pixels = read_pgm_bytes(image_item.getvalue())
        image = np.array(pixels, dtype=np.float32).reshape(height, width) * (255.0 / maximum)
        st.image(image.astype("uint8"), caption=caption, clamp=True, width=width)
        st.caption("Light = free, dark = occupied, gray = unknown. Use the numeric table as an accessible alternative.")
    except (ValueError, IndexError, ZeroDivisionError) as error:
        st.error(f"Could not preview this PGM map: {error}")
