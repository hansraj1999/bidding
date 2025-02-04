import uvicorn
import os
print(os.getenv("mongodb://fynd:fynd1234@docdb-2025-02-04-21-36-32.cluster-c302wsi4sxgz.ap-south-1.docdb.amazonaws.com:27017/?tls=true&tlsCAFile=global-bundle.pem&replicaSet=rs0&readPreference=secondaryPreferred&retryWrites=false"), "ofnonfonfon")

if __name__ == "__main__":
    uvicorn.run(
        "app:start_server", port=8000, host="0.0.0.0", reload=True, factory=True
    )