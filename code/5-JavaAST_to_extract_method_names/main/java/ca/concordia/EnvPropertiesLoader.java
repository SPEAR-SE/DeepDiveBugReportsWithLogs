package ca.concordia;
import java.io.IOException;
import java.io.InputStream;
import java.util.Properties;

public class EnvPropertiesLoader {
    private Properties secrets;

    public EnvPropertiesLoader() {
        secrets = new Properties();
        try (InputStream input = EnvPropertiesLoader.class.getResourceAsStream("env.properties")) {
            // load a properties file
            secrets.load(input);
        } catch (IOException ex) {
            ex.printStackTrace();
        }
    }

    public String getSecret(String key) {
        return secrets.getProperty(key);
    }
}
