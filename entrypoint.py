import uvicorn
import os
print(os.getenv("mongo_con"), "ofnonfonfon")

if __name__ == "__main__":
    uvicorn.run(
        "app:start_server", port=8000, host="0.0.0.0", reload=True, factory=True
    )