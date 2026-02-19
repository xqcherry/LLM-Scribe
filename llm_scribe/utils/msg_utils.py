def chunk_msgs(msgs, chunk_size=220, overlap=50):

    n = len(msgs)
    if n == 0:
        return []

    chunks = []
    i = 0
    while i < n:
        end = min(i + chunk_size, n)
        chunks.append(msgs[i:end])
        i += (chunk_size - overlap)

    return chunks