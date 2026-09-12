def process_buffer(buffer):
    lines = []

    while "\n" in buffer:
        line, buffer = buffer.split("\n", 1)

        if line.strip():
            lines.append(line)

    return lines, buffer


def test_complete_record():
    buffer = '{"reading_id": 1}\n'

    lines, remaining = process_buffer(buffer)

    assert lines == ['{"reading_id": 1}']
    assert remaining == ""

    print("COMPLETE RECORD: PASS")


def test_split_record():
    part1 = '{"reading_id": 1'
    part2 = '}\n'

    buffer = part1

    lines, remaining = process_buffer(buffer)

    assert lines == []
    assert remaining == part1

    buffer += part2

    lines, remaining = process_buffer(buffer)

    assert lines == ['{"reading_id": 1}']
    assert remaining == ""

    print("SPLIT RECORD: PASS")


def test_multiple_records():
    buffer = (
        '{"reading_id": 1}\n'
        '{"reading_id": 2}\n'
        '{"reading_id": 3}\n'
    )

    lines, remaining = process_buffer(buffer)

    assert lines == [
        '{"reading_id": 1}',
        '{"reading_id": 2}',
        '{"reading_id": 3}',
    ]

    assert remaining == ""

    print("MULTIPLE RECORDS: PASS")


def test_partial_last_record():
    buffer = (
        '{"reading_id": 1}\n'
        '{"reading_id": 2'
    )

    lines, remaining = process_buffer(buffer)

    assert lines == ['{"reading_id": 1}']
    assert remaining == '{"reading_id": 2'

    print("PARTIAL LAST RECORD: PASS")


test_complete_record()
test_split_record()
test_multiple_records()
test_partial_last_record()