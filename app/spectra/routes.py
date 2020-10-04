import base64
import rainflow
import pandas as pd
from matplotlib.figure import Figure
from flask import (Blueprint, render_template, url_for, flash,
                   redirect, abort, request, send_file)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from io import BytesIO
from app import db
from app.spectra.forms import SpectrumForm, SpectrumOptionsForm, SpectrumSaveForm
from app.models import Stress, Spectrum

spectra = Blueprint('spectra', __name__)


@spectra.route("/stress", methods=['GET', 'POST'])
@login_required
def stress():
    form = SpectrumForm()
    if form.validate_on_submit():
        f = form.title.data
        filename = secure_filename(f.filename)
        new_stress = Stress(title=filename, author=current_user, data=f.read())
        db.session.add(new_stress)
        db.session.commit()
        flash('File has been uploaded!', 'success')
        return redirect(url_for('spectra.stress'))
    page = request.args.get('page', 1, type=int)
    all_stress = Stress.query.filter_by(author=current_user) \
        .order_by(Stress.date_posted.desc()) \
        .paginate(page=page, per_page=8)
    return render_template("public/stress.html", files=all_stress, title='Stress', form=form)


@spectra.route('/stress/delete/<stress_id>/', methods=['GET', 'POST'])
def delete(stress_id):
    old_stress = Stress.query.get_or_404(stress_id)
    if old_stress.author != current_user:
        abort(403)
    db.session.delete(old_stress)
    db.session.commit()
    flash('Stress file has been deleted!', 'success')
    return redirect(url_for('spectra.stress'))


@spectra.route('/stress/review/<stress_id>/', methods=['GET', 'POST'])
def review(stress_id):
    current_stress = Stress.query.get_or_404(stress_id)
    if current_stress.author != current_user:
        abort(403)
    try:
        return send_file(BytesIO(current_stress.data), attachment_filename=current_stress.title, as_attachment=True)
    except FileNotFoundError:
        abort(404)


@spectra.route('/stress/run/<stress_id>/', methods=['GET', 'POST'])
def run(stress_id):
    run_stress = Stress.query.get_or_404(stress_id)
    if run_stress.author != current_user:
        abort(403)
    raw_data = str(run_stress.data, 'utf-8').split()
    stress_data = list(map(lambda z: float(z.replace(",", "")), raw_data))
    new_spectrum = []
    for i in rainflow.extract_cycles(stress_data):
        new_spectrum.append(i)
    spectrum_df = pd.DataFrame(new_spectrum)
    spectrum_df.columns = ['Stress Range', 'Mean Stress', 'Cycle Count', 'Step Start', 'Step End']
    spectrum_df = spectrum_df.reindex(columns=['Step Start', 'Step End', 'Cycle Count', 'Stress Range', 'Mean Stress'])
    spectrum_df['Max Stress'] = spectrum_df['Mean Stress'] + spectrum_df['Stress Range'] / 2
    spectrum_df['Min Stress'] = spectrum_df['Mean Stress'] - spectrum_df['Stress Range'] / 2
    spectrum_df = spectrum_df.round(2)
    cycle = []
    x = []
    y = []
    count_df = pd.DataFrame(cycle)
    form = SpectrumOptionsForm()
    if form.validate_on_submit():
        binsize = float(form.option.data)
        for i in rainflow.count_cycles(stress_data, binsize=binsize):
            cycle.append(i)
        count_df = pd.DataFrame(cycle)
        count_df.columns = ['Stress Range', 'Count']
    for (i, j) in cycle:
        x.append(i)
        y.append(j)
    fig = Figure()
    ax = fig.subplots(3, 1)
    ax[0].plot(stress_data)
    ax[0].set_xlim(0, len(stress_data) - 1)
    ax[0].set_title("Raw Data")
    ax[0].grid(True)
    ax[1].plot(spectrum_df['Mean Stress'], label='Mean Stress')
    ax[1].plot(spectrum_df['Max Stress'], label='Max Stress')
    ax[1].plot(spectrum_df['Min Stress'], label='Min Stress')
    ax[1].set_xlim(0, len(spectrum_df) - 1)
    ax[1].set_title("Spectrum")
    ax[1].legend()
    ax[1].grid(True)
    ax[2].grid(True)
    ax[2].set_title("Stress Range Count")
    ax[2].bar(x, y)
    ax[2].set_xlim(0)
    img = BytesIO()
    fig.tight_layout()
    fig.set_figheight(12)
    fig.set_figwidth(8)
    fig.savefig(img, format="png")
    plot = base64.b64encode(img.getbuffer()).decode("ascii")
    spec_form = SpectrumSaveForm()
    if spec_form.validate_on_submit():
        f = count_df.to_csv('spec_form.title.data.csv')
        filename = secure_filename(f.filename)
        new_spectrum = Spectrum(title=filename, author=current_user, data=f.read())
        db.session.add(new_spectrum)
        db.session.commit()
        flash('File has been saved!', 'success')
        return redirect(url_for('spectra.spectrum'))
    return render_template('public/new_spectrum.html', spec=[spectrum_df.to_html(header='true')],
                           count=[count_df.to_html(header='true')], raw_stress=run_stress.title,
                           form=form, spec_form=spec_form, plot=plot)


@spectra.route("/spectrum", methods=['GET', 'POST'])
@login_required
def spectrum():
    form = SpectrumSaveForm()
    if form.validate_on_submit():
        f = form.title.data
        filename = secure_filename(f.filename)
        new_spectrum = Spectrum(title=filename, author=current_user, data=f.read())
        db.session.add(new_spectrum)
        db.session.commit()
        flash('File has been saved!', 'success')
        return redirect(url_for('spectra.spectrum'))
    page = request.args.get('page', 1, type=int)
    all_spectrum = Spectrum.query.filter_by(author=current_user) \
        .order_by(Spectrum.date_posted.desc()) \
        .paginate(page=page, per_page=8)
    return render_template("public/spectrum.html", files=all_spectrum, title='Spectrum', form=form)
