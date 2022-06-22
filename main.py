from flask import Flask, render_template, request, send_file, jsonify, Response
from io import BytesIO
import os
import uuid

import pandas as pd
from pandas import *
import numpy as np

app = Flask(__name__)
app.static_folder = './static'
app.config['UPLOAD_FOLDER'] = 'files'


@app.route('/')
def get_page():
    return render_template("index.html")


@app.route('/upload', methods=["POST", "GET"])
def upload_file():
    if request.method == "POST":
        file = request.files['file']
        if file:
            data_reg_answer_18_19 = pd.read_csv(BytesIO(file.read()))

            # Удалить ненужные колонки из данных регистрации

            data_reg_answer_18_19 = data_reg_answer_18_19.drop(['Отметка времени',
                                                                'Укажите возможную форму Вашего участия в работе ГМО',
                                                                'Даю согласие на обработку персональных данных',
                                                                'Укажите Ваш уровень владения информационными технологиями'],
                                                               axis=1)

            mas_fio = data_reg_answer_18_19['Укажите Ваши фамилию, имя и отчество']

            # удаление ОДИНАКОВЫХ ФИО из набора данных в файле регистрации

            new_data_reg_answer_18_19 = pd.DataFrame()
            new_data_reg_answer_18_19 = data_reg_answer_18_19.drop_duplicates(
                subset=['Укажите Ваши фамилию, имя и отчество'])

            # все Nan заменяем на ?, только после этого все буквы делаем маленькими

            new_data_reg_answer_18_19.fillna('?',
                                             inplace=True)  # inplace=True, чтобы набор изменился после (обновился) замены
            new_data_reg_answer_18_19['Укажите Ваши фамилию, имя и отчество'] = new_data_reg_answer_18_19[
                'Укажите Ваши фамилию, имя и отчество'].str.lower()
            new_data_reg_answer_18_19['Укажите Вашу дату рождения'] = new_data_reg_answer_18_19[
                'Укажите Вашу дату рождения'].str.lower()
            new_data_reg_answer_18_19['Укажите Вашу должность'] = new_data_reg_answer_18_19[
                'Укажите Вашу должность'].str.lower()
            new_data_reg_answer_18_19['Укажите место Вашей работы'] = new_data_reg_answer_18_19[
                'Укажите место Вашей работы'].str.lower()
            new_data_reg_answer_18_19['Укажите Вашу квалификационную категорию'] = new_data_reg_answer_18_19[
                'Укажите Вашу квалификационную категорию'].str.lower()
            new_data_reg_answer_18_19['Выберите из списка наименование ГМО'] = new_data_reg_answer_18_19[
                'Выберите из списка наименование ГМО'].str.lower()
            new_data_reg_answer_18_19['Укажите значимые для Вас темы в работе ГМО'] = new_data_reg_answer_18_19[
                'Укажите значимые для Вас темы в работе ГМО'].str.lower()

            # создание датафрейма data_reg_answer_18_19_drop_dict, в котором будем учреждения и должности заменять цифрами

            data_reg_answer_17_18_drop_dict = pd.DataFrame()
            data_reg_answer_17_18_drop_dict = new_data_reg_answer_18_19.copy(deep=True)

            job_cop_1 = data_reg_answer_17_18_drop_dict.drop(
                ['Укажите Вашу квалификационную категорию', 'Укажите место Вашей работы', 'Укажите Вашу дату рождения'],
                axis=1)
            bou = {'сош': 1, 'гимн': 1, 'лицей': 1, 'общеобразовательная': 1, 'детский сад': 2, 'сад': 2, 'боу': 3,
                   'удо': 3, 'станция': 3, 'гцппмсп': 3, 'доу': 3, 'бук': 3, 'ано': 3, 'до': 3}

            # Замена названий учреждений цифрами в датафрейме data_reg_answer_18_19_drop_dict

            for key, val in bou.items():
                data_reg_answer_17_18_drop_dict['Укажите место Вашей работы'] = data_reg_answer_17_18_drop_dict[
                    'Укажите место Вашей работы'].replace(to_replace=r'.*' + key + '.*', value=val, regex=True)

            # приведение всех данных колонки к типу int64 (проверить для каждой из тех колонок, где должны быть цифры)

            data_reg_answer_17_18_drop_dict['Укажите место Вашей работы'].astype('int64')
            dolj = {'дир': 1, 'замдир': 1, 'завуч': 1, 'зав отделом': 1, 'педаг': 3, 'препод': 3, 'учитель': 3,
                    'логопед': 3, 'психолог': 3, 'воспитатель': 3, 'хореограф': 3, 'метод': 2,
                    'концер': 4, 'библ': 4, 'муз': 4, '?': 3, 'заведующий': 1, 'хор': 4, 'инструктор': 3}

            # Замена названий учреждений цифрами в датафрейме data_reg_answer_18_19_drop_dict

            for key, val in dolj.items():
                data_reg_answer_17_18_drop_dict['Укажите Вашу должность'] = data_reg_answer_17_18_drop_dict[
                    'Укажите Вашу должность'].replace(to_replace=r'.*' + key + '.*', value=val, regex=True)

            # приведение всех данных колонки к типу int64 (проверить для каждой из тех колонок, где должны быть цифры)

            data_reg_answer_17_18_drop_dict['Укажите Вашу должность'].astype('int64')

            # Замена должностей цифрами: 1 - администрация (директора, замдиректора, завуч, зав отделом, зам)
            # 2 - педагоги (педаг, препод, учитель, логопед, психолог, воспитатель, хореограф)
            # 3 - методисты (метод)
            # 4 - концертмейстер, библиотекарь, музейный методист (концерт, биб, муз)

            # final age - итоговый датафрейм со всеми людьми, которым 45 или больше лет

            age = data_reg_answer_17_18_drop_dict
            age = age.drop(
                ['Укажите Вашу должность', 'Укажите место Вашей работы', 'Укажите Вашу квалификационную категорию',
                 'Укажите Ваш контактный телефон', 'Укажите адрес Вашей электронной почты',
                 'Выберите из списка наименование ГМО', 'Укажите значимые для Вас темы в работе ГМО'], axis=1)
            age.rename(columns={'Укажите Вашу дату рождения': 'Возраст'}, inplace=True)
            a = age['Возраст']
            a = a.str.slice(start=6)
            a = a.astype('int64')
            a = 2022 - a
            age['Возраст'] = a
            final_age = age.loc[age['Возраст'] > 44]
            cvalification = data_reg_answer_17_18_drop_dict.loc[
                data_reg_answer_17_18_drop_dict['Укажите Вашу квалификационную категорию'] == 'первая']
            cvalification = cvalification.drop(
                ['Укажите Вашу дату рождения', 'Укажите Вашу должность', 'Укажите место Вашей работы',
                 'Укажите Ваш контактный телефон', 'Укажите адрес Вашей электронной почты',
                 'Выберите из списка наименование ГМО', 'Укажите значимые для Вас темы в работе ГМО'], axis=1)
            cvalification.rename(columns={'Укажите Вашу квалификационную категорию': 'Квалификационная категория'},
                                 inplace=True)
            job_test = data_reg_answer_17_18_drop_dict
            job_test = job_test.drop(
                ['Укажите Вашу квалификационную категорию', 'Укажите место Вашей работы', 'Укажите Вашу дату рождения',
                 'Укажите Ваш контактный телефон', 'Укажите адрес Вашей электронной почты',
                 'Выберите из списка наименование ГМО', 'Укажите значимые для Вас темы в работе ГМО'], axis=1)
            job_cop_2 = job_test
            job_test['Укажите Вашу должность'] = np.where((job_test['Укажите Вашу должность'] == 2), 0,
                                                          job_test['Укажите Вашу должность'])
            job_test['Укажите Вашу должность'] = np.where((job_test['Укажите Вашу должность'] == 4), 0,
                                                          job_test['Укажите Вашу должность'])
            final_job = job_test
            final_job = final_job.loc[final_job['Укажите Вашу должность'] != 0]
            final_job.rename(columns={'Укажите Вашу должность': 'Должность'}, inplace=True)
            final_job['Должность'] = final_job['Должность'].astype('str')
            dolj = {'1': 'Администрация', '3': 'Методист'}
            for key, val in dolj.items():
                final_job['Должность'] = final_job['Должность'].replace(to_replace=r'.*' + key + '.*', value=val,
                                                                        regex=True)
            final_age = final_age.drop(['№'], axis=1)
            final_age = final_age.reset_index()
            final_age = final_age.drop(['index'], axis=1)
            cvalification = cvalification.drop(['№'], axis=1)
            cvalification = cvalification.reset_index()
            cvalification = cvalification.drop(['index'], axis=1)
            final_job = final_job.drop(['№'], axis=1)
            final_job = final_job.reset_index()
            final_job = final_job.drop(['index'], axis=1)
            age_cop = final_age
            cv_cop = cvalification
            job_cop = final_job
            the_desc = age_cop.merge(cv_cop, how='inner')
            job_cop_2 = data_reg_answer_17_18_drop_dict.drop(
                ['Укажите Вашу квалификационную категорию', 'Укажите место Вашей работы', 'Укажите Вашу дату рождения',
                 'Укажите Ваш контактный телефон', 'Укажите адрес Вашей электронной почты',
                 'Выберите из списка наименование ГМО', 'Укажите значимые для Вас темы в работе ГМО'], axis=1)
            the_final_desc = the_desc.merge(job_cop_2, how='left')
            the_final_desc = the_final_desc.sort_values(by='Укажите Вашу должность', ignore_index=True)
            the_final_desc = the_final_desc.drop(['№'], axis=1)
            the_final_desc = the_final_desc.rename(columns={'Укажите Вашу должность': 'b'})
            the_final_desc = the_final_desc.drop('b', axis=1)
            the_final_desc = the_final_desc.merge(job_cop_1, how='left')
            the_final_desc = the_final_desc.drop('№', axis=1)

            # под конец мы имеем 3 таблицы: final_age - все люди старше 45 лет final_job - выборка людей, с самыми важными должностями
            # cvalification - все люди с первой квалификационной категорией
            # the_final_desc - итоговая таблица с людьми, подходящими по всем самым важным критериям

            the_final_desc = the_final_desc.rename(columns={'Укажите Вашу должность': 'Должность'})
            the_final_desc = the_final_desc.rename(columns={'Укажите Ваш контактный телефон': 'Телефон'})
            the_final_desc = the_final_desc.rename(columns={'Укажите адрес Вашей электронной почты': 'Эл. почта'})
            the_final_desc = the_final_desc.rename(columns={'Выберите из списка наименование ГМО': 'ГМО'})
            the_final_desc = the_final_desc.rename(columns={'Укажите значимые для Вас темы в работе ГМО': 'Темы'})
            the_final_desc = the_final_desc.rename(columns={'Укажите Ваши фамилию, имя и отчество': 'ФИО'})
            for i in range(len(the_final_desc)):
                the_final_desc = the_final_desc.replace(to_replace=the_final_desc['ФИО'].loc[i],
                                                        value=the_final_desc['ФИО'].loc[i].title(), regex=True)
                the_final_desc = the_final_desc.replace(to_replace=the_final_desc['Должность'].loc[i],
                                                        value=the_final_desc['Должность'].loc[i].capitalize(),
                                                        regex=True)
                the_final_desc = the_final_desc.replace(to_replace=the_final_desc['Квалификационная категория'].loc[i],
                                                        value=the_final_desc['Квалификационная категория'].loc[
                                                            i].capitalize(), regex=True)
                the_final_desc = the_final_desc.replace(to_replace=the_final_desc['ГМО'].loc[i],
                                                        value=the_final_desc['ГМО'].loc[i].capitalize(), regex=True)
                the_final_desc = the_final_desc.replace(to_replace=the_final_desc['Темы'].loc[i],
                                                        value=the_final_desc['Темы'].loc[i].capitalize(), regex=True)

            fileName = uuid.uuid4().hex
            resp = Response(the_final_desc.to_csv(encoding='cp-1251'), mimetype='text/csv')
            resp.headers.set("Content-Disposition", "attachment", filename=f"{fileName}.csv", charset='cp-1251')
            return resp
            # return render_template('check.html')
        # return render_template('index.html')
    # return render_template('index.html')


@app.route('/download')
def download():
    name = request.args.get('name')
    return send_file(f'files/{name}.csv', as_attachment=True, attachment_filename=f'{name}.csv', mimetype='file/csv')


if __name__ == '__main__':
    app.run(debug = True)
