import joblib
import os


def analyze_model(model_path):

    # ==========================================
    # CHECK MODEL FILE
    # ==========================================

    if not os.path.exists(model_path):

        print("\nModel file not found:")
        print(model_path)

        return None


    # ==========================================
    # CHECK FILE EXTENSION
    # ==========================================

    extension = os.path.splitext(
        model_path
    )[1].lower()

    if extension not in [".joblib", ".pkl"]:

        print(
            "\nUnsupported model file format."
        )

        print(
            "Supported formats: .joblib, .pkl"
        )

        return None


    # ==========================================
    # LOAD MODEL
    # ==========================================

    try:

        model = joblib.load(
            model_path
        )

    except Exception as e:

        print(
            "\nUnable to load model."
        )

        print(
            "Error:",
            e
        )

        return None


    # ==========================================
    # BASIC MODEL INFORMATION
    # ==========================================

    model_info = {

        "model_path": model_path,

        "model_type": type(model).__name__,

        "model_size_kb": round(
            os.path.getsize(model_path) / 1024,
            2
        ),

        "features": 0,

        "classes": 0,

        "components": [],

        "vectorizer": None,

        "classifier": None,

        "supported": True
    }


    # ==========================================
    # CHECK PIPELINE
    # ==========================================

    if hasattr(model, "steps"):

        for name, component in model.steps:

            component_type = (
                type(component).__name__
            )

            model_info["components"].append(
                component_type
            )


            # ------------------------------
            # Vectorizer
            # ------------------------------

            if "Vectorizer" in component_type:

                model_info["vectorizer"] = (
                    component_type
                )

                if hasattr(
                    component,
                    "vocabulary_"
                ):

                    model_info["features"] = (
                        len(
                            component.vocabulary_
                        )
                    )


            # ------------------------------
            # Classifier
            # ------------------------------

            if hasattr(
                component,
                "classes_"
            ):

                model_info["classifier"] = (
                    component_type
                )

                model_info["classes"] = (
                    len(
                        component.classes_
                    )
                )


    # ==========================================
    # NON-PIPELINE MODEL
    # ==========================================

    else:

        model_info["components"].append(
            type(model).__name__
        )


        # Check whether model has classes

        if hasattr(
            model,
            "classes_"
        ):

            model_info["classes"] = len(
                model.classes_
            )


        # Check common feature attributes

        if hasattr(
            model,
            "n_features_in_"
        ):

            model_info["features"] = (
                model.n_features_in_
            )


    # ==========================================
    # BASIC MODEL COMPATIBILITY CHECK
    # ==========================================

    supported_model_types = [

        "Pipeline",

        "LogisticRegression",

        "LinearRegression",

        "Ridge",

        "Lasso",

        "DecisionTreeClassifier",

        "DecisionTreeRegressor",

        "RandomForestClassifier",

        "RandomForestRegressor",

        "GradientBoostingClassifier",

        "GradientBoostingRegressor",

        "MultinomialNB",

        "GaussianNB",

        "SVC",

        "SVR",

        "KNeighborsClassifier",

        "KNeighborsRegressor"
    ]


    if model_info["model_type"] not in supported_model_types:

        model_info["supported"] = False


    return model_info


# ==========================================
# TEST MODEL ANALYZER
# ==========================================

if __name__ == "__main__":

    MODEL_PATH = "spam_classifier.joblib"

    result = analyze_model(
        MODEL_PATH
    )


    if result:

        print(
            "\n===== MODEL ANALYSIS ====="
        )

        print(
            "Model path:",
            result["model_path"]
        )

        print(
            "Model type:",
            result["model_type"]
        )

        print(
            "Model size:",
            result["model_size_kb"],
            "KB"
        )

        print(
            "Number of features:",
            result["features"]
        )

        print(
            "Number of classes:",
            result["classes"]
        )

        print(
            "Vectorizer:",
            result["vectorizer"]
        )

        print(
            "Classifier:",
            result["classifier"]
        )

        print(
            "Supported:",
            result["supported"]
        )


        print(
            "\nComponents:"
        )

        for component in result["components"]:

            print(
                "-",
                component
            )


        print(
            "\nModel analyzed successfully."
        )