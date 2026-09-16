window.HINDSFOOT_PUBLIC_CONFIG = Object.freeze({
  loginUrl: location.port === "8010"
    ? `${location.protocol}//${location.hostname}:5000/login`
    : "",
  demonstrationRequestEndpoint: "",
  contactEmail: "",
  privacyPolicyUrl: "privacy.html"
});
