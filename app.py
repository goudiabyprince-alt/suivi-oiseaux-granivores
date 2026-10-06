"""
Application de suivi des dortoirs d'oiseaux granivores
--------------------------------------------------------
Enregistre la position finale des individus tagués (ex: Q1 à Q5),
les affiche automatiquement sur une carte, génère un lien direct
vers Google Maps pour l'équipe terrain, et permet de consigner
la confirmation par drone (effectif estimé, notes).

Auteur : Abdou Goudiaby
"""

import json
import os
from datetime import datetime

import folium
import streamlit as st
from streamlit_folium import st_folium

# ----------------------------------------------------------------
# Configuration et stockage des données
# ----------------------------------------------------------------

DOSSIER_DONNEES = os.path.dirname(os.path.abspath(__file__))
FICHIER_OBSERVATIONS = os.path.join(DOSSIER_DONNEES, "observations.json")
FICHIER_SITES = os.path.join(DOSSIER_DONNEES, "sites_confirmes.json")

# Centre de carte par défaut : Vallée du Fleuve Sénégal (Saint-Louis)
CENTRE_CARTE_DEFAUT = [16.0179, -16.4896]

COULEURS_OISEAUX = {
    "Q1": "red",
    "Q2": "blue",
    "Q3": "green",
    "Q4": "purple",
    "Q5": "orange",
}


def charger_json(chemin):
    """Charge une liste depuis un fichier JSON, ou renvoie une liste vide si le fichier n'existe pas encore."""
    if os.path.exists(chemin):
        with open(chemin, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def sauvegarder_json(chemin, donnees):
    """Enregistre une liste dans un fichier JSON, avec indentation lisible."""
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(donnees, f, ensure_ascii=False, indent=2)


def creer_observation(id_oiseau, latitude, longitude, date_obs, heure_obs, source):
    """Construit un dictionnaire représentant une observation (position d'un oiseau)."""
    return {
        "id_oiseau": id_oiseau,
        "latitude": latitude,
        "longitude": longitude,
        "date": date_obs,
        "heure": heure_obs,
        "source": source,
        "enregistre_le": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }


def lien_google_maps(latitude, longitude):
    """Construit un lien Google Maps pointant directement sur une position GPS."""
    return f"https://www.google.com/maps?q={latitude},{longitude}"


# ----------------------------------------------------------------
# Chargement des données en mémoire (session)
# ----------------------------------------------------------------

if "observations" not in st.session_state:
    st.session_state.observations = charger_json(FICHIER_OBSERVATIONS)

if "sites_confirmes" not in st.session_state:
    st.session_state.sites_confirmes = charger_json(FICHIER_SITES)


# ----------------------------------------------------------------
# Interface
# ----------------------------------------------------------------

st.set_page_config(page_title="Suivi des dortoirs d'oiseaux", page_icon="🦜", layout="wide")

st.title("🦜 Suivi des dortoirs d'oiseaux granivores")
st.caption("Localisation en temps réel des dortoirs — Vallée du Fleuve Sénégal")

onglet_saisie, onglet_carte, onglet_drone, onglet_historique = st.tabs(
    ["➕ Nouvelle position", "🗺️ Carte", "🚁 Confirmation drone", "📋 Historique"]
)

# ------------------------------------------------------------
# Onglet 1 : saisie d'une nouvelle position
# ------------------------------------------------------------
with onglet_saisie:
    st.subheader("Enregistrer la position d'un oiseau tagué")

    with st.form("formulaire_observation", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            id_oiseau = st.selectbox("Identifiant de l'oiseau", ["Q1", "Q2", "Q3", "Q4", "Q5"])
            latitude = st.number_input("Latitude", value=16.0179, format="%.6f")
            longitude = st.number_input("Longitude", value=-16.4896, format="%.6f")

        with col2:
            date_obs = st.date_input("Date", value=datetime.now())
            heure_obs = st.time_input("Heure", value=datetime.now())
            source = st.radio("Source de la position", ["Manuelle (récepteur portable)", "Station fixe"])

        valider = st.form_submit_button("Enregistrer la position", use_container_width=True)

        if valider:
            nouvelle_observation = creer_observation(
                id_oiseau,
                latitude,
                longitude,
                date_obs.strftime("%Y-%m-%d"),
                heure_obs.strftime("%H:%M"),
                source,
            )
            st.session_state.observations.append(nouvelle_observation)
            sauvegarder_json(FICHIER_OBSERVATIONS, st.session_state.observations)
            st.success(f"Position de {id_oiseau} enregistrée.")

    if st.session_state.observations:
        derniere = st.session_state.observations[-1]
        st.info(
            f"Dernière position enregistrée : **{derniere['id_oiseau']}** "
            f"à ({derniere['latitude']}, {derniere['longitude']}) le {derniere['date']} à {derniere['heure']}"
        )
        st.link_button("📍 Ouvrir cette position dans Google Maps", lien_google_maps(derniere["latitude"], derniere["longitude"]))


# ------------------------------------------------------------
# Onglet 2 : carte
# ------------------------------------------------------------
with onglet_carte:
    st.subheader("Position des oiseaux tagués")

    observations = st.session_state.observations

    if not observations:
        st.warning("Aucune observation enregistrée pour le moment.")
    else:
        # Centre la carte sur la dernière observation
        derniere = observations[-1]
        carte = folium.Map(location=[derniere["latitude"], derniere["longitude"]], zoom_start=13)

        for obs in observations:
            couleur = COULEURS_OISEAUX.get(obs["id_oiseau"], "gray")
            popup_texte = (
                f"<b>{obs['id_oiseau']}</b><br>"
                f"{obs['date']} à {obs['heure']}<br>"
                f"Source : {obs['source']}<br>"
                f"<a href='{lien_google_maps(obs['latitude'], obs['longitude'])}' target='_blank'>Ouvrir dans Google Maps</a>"
            )
            folium.Marker(
                location=[obs["latitude"], obs["longitude"]],
                popup=folium.Popup(popup_texte, max_width=250),
                tooltip=obs["id_oiseau"],
                icon=folium.Icon(color=couleur, icon="info-sign"),
            ).add_to(carte)

        # Marqueurs des sites déjà confirmés au drone
        for site in st.session_state.sites_confirmes:
            folium.CircleMarker(
                location=[site["latitude"], site["longitude"]],
                radius=15,
                color="black",
                fill=True,
                fill_opacity=0.15,
                popup=f"Dortoir confirmé : {site['nom_site']} (~{site['effectif_estime']} individus)",
                tooltip="Dortoir confirmé",
            ).add_to(carte)

        st_folium(carte, width=None, height=550, use_container_width=True)

        # Alerte simple de convergence : plusieurs oiseaux du jour proches les uns des autres
        aujourdhui = datetime.now().strftime("%Y-%m-%d")
        obs_du_jour = [o for o in observations if o["date"] == aujourdhui]
        ids_distincts = set(o["id_oiseau"] for o in obs_du_jour)
        if len(ids_distincts) >= 3:
            st.success(
                f"⚠️ {len(ids_distincts)} oiseaux différents positionnés aujourd'hui. "
                "Si leurs points sont proches sur la carte, c'est un bon indice de dortoir — "
                "direction la vérification au drone."
            )


# ------------------------------------------------------------
# Onglet 3 : confirmation drone
# ------------------------------------------------------------
with onglet_drone:
    st.subheader("Consigner la confirmation par drone")

    with st.form("formulaire_drone", clear_on_submit=True):
        nom_site = st.text_input("Nom ou repère du site (ex: Bosquet Nord Ross-Béthio)")
        col1, col2 = st.columns(2)
        with col1:
            lat_site = st.number_input("Latitude du site", value=16.0179, format="%.6f", key="lat_drone")
        with col2:
            lon_site = st.number_input("Longitude du site", value=-16.4896, format="%.6f", key="lon_drone")

        effectif_estime = st.number_input("Effectif estimé (nombre d'individus)", min_value=0, step=100)
        notes = st.text_area("Notes (comportement observé, qualité de la vue, etc.)")

        confirmer = st.form_submit_button("Enregistrer la confirmation", use_container_width=True)

        if confirmer:
            nouveau_site = {
                "nom_site": nom_site,
                "latitude": lat_site,
                "longitude": lon_site,
                "effectif_estime": effectif_estime,
                "notes": notes,
                "confirme_le": datetime.now().strftime("%Y-%m-%d %H:%M"),
            }
            st.session_state.sites_confirmes.append(nouveau_site)
            sauvegarder_json(FICHIER_SITES, st.session_state.sites_confirmes)
            st.success(f"Dortoir « {nom_site} » enregistré avec un effectif estimé de {effectif_estime} individus.")
            st.info("Ce site apparaît maintenant sur la carte. Il peut être transmis à la DPV.")

    if st.session_state.sites_confirmes:
        st.subheader("Dortoirs confirmés")
        for site in reversed(st.session_state.sites_confirmes):
            with st.container(border=True):
                st.markdown(f"**{site['nom_site']}** — confirmé le {site['confirme_le']}")
                st.write(f"Effectif estimé : {site['effectif_estime']} individus")
                if site["notes"]:
                    st.write(f"Notes : {site['notes']}")
                st.link_button("📍 Ouvrir dans Google Maps", lien_google_maps(site["latitude"], site["longitude"]))


# ------------------------------------------------------------
# Onglet 4 : historique
# ------------------------------------------------------------
with onglet_historique:
    st.subheader("Historique des positions enregistrées")

    if not st.session_state.observations:
        st.warning("Aucune observation enregistrée pour le moment.")
    else:
        oiseau_filtre = st.selectbox(
            "Filtrer par oiseau", ["Tous"] + sorted(set(o["id_oiseau"] for o in st.session_state.observations))
        )

        donnees_affichees = st.session_state.observations
        if oiseau_filtre != "Tous":
            donnees_affichees = [o for o in donnees_affichees if o["id_oiseau"] == oiseau_filtre]

        st.dataframe(
            donnees_affichees,
            use_container_width=True,
            column_config={
                "id_oiseau": "Oiseau",
                "latitude": "Latitude",
                "longitude": "Longitude",
                "date": "Date",
                "heure": "Heure",
                "source": "Source",
                "enregistre_le": "Enregistré le",
            },
        )

        if st.button("🗑️ Effacer tout l'historique (observations)", type="secondary"):
            st.session_state.observations = []
            sauvegarder_json(FICHIER_OBSERVATIONS, [])
            st.rerun()
