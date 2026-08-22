import argparse
import json
import threading
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor


URL = "http://127.0.0.1:3000/api/reset-password"

barrier = threading.Barrier(3)


def send_request(label, password, student_id):
    body = json.dumps({
        "email": "poola-api-077@example.test",
        "resetToken": "100077",
        "newPassword": password,
    }).encode("utf-8")

    request = urllib.request.Request(
        URL,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-Student-Id": student_id,
        },
    )

    # Both worker threads stop here.
    barrier.wait()

    try:
        with urllib.request.urlopen(request) as response:
            return {
                "request": label,
                "password": password,
                "status": response.status,
                "body": response.read().decode("utf-8"),
            }
    except urllib.error.HTTPError as exc:
        return {
            "request": label,
            "password": password,
            "status": exc.code,
            "body": exc.read().decode("utf-8"),
        }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--student-id", required=True)
    args = parser.parse_args()

    with ThreadPoolExecutor(max_workers=2) as executor:
        future_a = executor.submit(
            send_request,
            "A",
            "ConcurrentReset1!",
            args.student_id,
        )
        future_b = executor.submit(
            send_request,
            "B",
            "ConcurrentReset2!",
            args.student_id,
        )

        # Release A and B together.
        barrier.wait()

        result_a = future_a.result()
        result_b = future_b.result()

    print(json.dumps([result_a, result_b], indent=2))

    successes = sum(
        result["status"] == 200
        for result in (result_a, result_b)
    )

    print()
    if successes == 1:
        print("RESULT: PASS - exactly one reset succeeded.")
    elif successes == 2:
        print("RESULT: FAIL - both concurrent resets succeeded.")
    else:
        print("RESULT: INVESTIGATE - neither reset succeeded.")


if __name__ == "__main__":
    main()