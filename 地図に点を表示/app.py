from flask import Flask, render_template
import csv

app = Flask(__name__)

@app.route('/')
def index():
    coordinates = []
    with open('S-net.csv', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            lat = float(row['lat'])
            lon = float(row['lon'])
            coordinates.append([lat, lon])
    return render_template('index.html', coordinates=coordinates)

if __name__ == '__main__':
    app.run(debug=True)
