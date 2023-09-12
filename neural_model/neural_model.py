import csv
import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense

CSV_FILE = "../users/users.csv"


# ---------- Работа с CSV ----------

def read_csv():
    data = []
    with open(CSV_FILE, 'r') as file:
        reader = csv.reader(file)
        next(reader)  # Пропускаем заголовок
        for row in reader:
            data.append(row)
    return data


def get_user_data(user_id):
    with open(CSV_FILE, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            if row[0] == user_id:
                return row
    return None


def update_activity_score(user_id, score):
    data = []
    with open(CSV_FILE, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            if row[0] == user_id:
                row[5] = score  # предполагаем, что активность - это 6-й столбец в CSV
                data.append(row)
            else:
                data.append(row)

    with open(CSV_FILE, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(data)

def update_activity_score_to_csv(user_id, score):
    data = []
    user_updated = False

    with open(CSV_FILE, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            if row[0] == user_id:
                data.append([user_id] + row[1:5] + [score])
                user_updated = True
            else:
                data.append(row)

    if not user_updated:
        data.append([user_id, 0, 0, 0, 0, score])

    with open(CSV_FILE, 'w') as file:
        writer = csv.writer(file)
        writer.writerows(data)

# ---------- Создание и обучение модели ----------

def build_model():
    model = Sequential()
    model.add(Dense(32, activation='relu', input_dim=4))
    model.add(Dense(16, activation='relu'))
    model.add(Dense(1, activation='linear'))
    model.compile(optimizer='adam', loss='mse')
    return model


def train_model(model):
    data = read_csv()

    X = [list(map(float, row[1:5])) for row in data]
    Y = [float(row[5]) if len(row) > 5 else 0.0 for row in
         data]

    model.fit(X, Y, epochs=10, batch_size=1, verbose=0)


def evaluate_user(user_id, model):
    user_data = get_user_data(user_id)

    if user_data is None:
        print(f"Нет данных для пользователя с ID {user_id}")
        return 0.0

    activity_vector = list(map(float, user_data[1:5]))
    activity_score = model.predict([activity_vector])[0][0]
    update_activity_score_to_csv(user_id, activity_score)

    return activity_score


def model_build(user_id):
    model = build_model()
    train_model(model)
    score = evaluate_user(user_id, model)
    print(score)


if __name__ == "__main__":
    user_id = '589171119'
    model_build(user_id)