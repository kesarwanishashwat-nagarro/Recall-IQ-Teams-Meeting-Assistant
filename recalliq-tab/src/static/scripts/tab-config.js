// Import the Microsoft Teams SDK
const { app, pages } = window.microsoftTeams;

// Initialize the Microsoft Teams SDK
app.initialize().then(() => {
  /**
   * Register the save handler to store the configuration
   */
  pages.config.registerOnSaveHandler((saveEvent) => {
    // const baseUrl = `https://${window.location.hostname}:${window.location.port}`;
    const baseUrl = window.location.origin;
    // Set the configuration for the tab
    pages.config
      .setConfig({
        suggestedDisplayName: "RecallIQ",
        entityId: "Test",
        contentUrl: baseUrl + "/tab",
        websiteUrl: baseUrl + "/tab",
      })
      .then(() => {
        saveEvent.notifySuccess();
      });
  });

  /**
   * Set the validity state to true, enabling the save button
   */
  pages.config.setValidityState(true);

  // Hide the loading indicator by notifying success
  app.notifySuccess();
});
