import logging
import time
import grpc
from module_a.send_event import EventSender


def dummy_burst_sender():
    """Continuously sends events in bursts: 2 messages / 1s then sleep 3s."""
    counter = 0
    counter_id = 0
    sender = EventSender()  # (1) CREATE SENDER
    try:
        while True:
            counter += 1
            print(f"counter: {counter}")
            if counter % 5 == 0:
                for _ in range(2):
                    counter_id += 1
                    payload = {"text": f"Hello number {counter_id}"} # (2) Generate payload (event data as a dict[str, str])
                    logging.info(f"➡️  Forwarding text {counter_id} (id={str(counter_id)})")
                    try:
                        sender.send_async(str(counter_id), payload) # (3) SEND EVENT
                    except grpc.RpcError as e:
                        logging.error(f"❌ Failed to send event: {e}")
                    time.sleep(0.5) 
                logging.info("✅ Burst finished. Sleeping for 3 seconds…")

            time.sleep(3)
    except KeyboardInterrupt:
        logging.info("Dummy sender stopped by user.")


if __name__ == "__main__":
    dummy_burst_sender() 