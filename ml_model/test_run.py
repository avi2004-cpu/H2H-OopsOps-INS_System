from data_loader import load_data
from model import AnomalyDetector

data_path = "../network_simulation/data/network_data.csv"

df = load_data(data_path)

detector = AnomalyDetector()
detector.train(df, ['traffic', 'signal'])

result = detector.predict(df)

print(result.head())