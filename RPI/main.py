import config as Config
import mongodb as MongoDB
import mqtt_broker as Mosquito

def main():
    try:
        Config.run()
        Mosquito.run()
    except Exception as e:
        print(f"Error during setup: {e}")


if __name__ == "__main__":
    main()
