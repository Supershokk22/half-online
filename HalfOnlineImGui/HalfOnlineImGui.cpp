#include <Mod/CppUserModBase.hpp>
#include <filesystem>
#include <fstream>
#include <cstdlib>
#include <string>
#include <format>

// Half Online ImGui admin surface — assinado: shokk
// This is intentionally a bridge-only UI. It never calls engine objects from
// the ImGui render callback; commands are consumed by the existing Lua bridge
// on the game thread.
class HalfOnlineImGui final : public RC::CppUserModBase {
    std::filesystem::path bridge_;
    std::string last_status_{"Aguardando sessão"};

    void command(const char* value) {
        std::error_code ec;
        std::filesystem::create_directories(bridge_, ec);
        std::ofstream out(bridge_ / "mp_openworld_control.txt", std::ios::trunc);
        if (!out) { last_status_ = "Não foi possível escrever no bridge"; return; }
        out << value << "\n";
        last_status_ = std::format("Comando enviado: {}", value);
    }

    void render() {
        ImGui::Text("HALF ONLINE");
        ImGui::Text("Painel administrativo — assinado: shokk");
        ImGui::Separator();
        ImGui::Text("%s", last_status_.c_str());
        if (ImGui::Button("Spawn bot marcador")) command("game spawn_bot");
        ImGui::SameLine();
        if (ImGui::Button("Spawn item marcador")) command("game spawn_item");
        if (ImGui::Button("Limpar marcadores")) command("game clear_spawns");
        ImGui::Separator();
        ImGui::TextWrapped("Ações nativas de combate permanecem bloqueadas até validação da classe do jogo.");
    }

public:
    HalfOnlineImGui() {
        ModName = STR("HalfOnlineImGui");
        ModVersion = STR("0.1.0");
        ModDescription = STR("ImGui admin panel for Half Online");
        ModAuthors = STR("shokk");
        bridge_ = std::filesystem::path(std::getenv("LOCALAPPDATA") ? std::getenv("LOCALAPPDATA") : ".")
            / "HalfSwordUE5" / "Saved" / "HalfSwordOnlineReal";
        UE4SS_ENABLE_IMGUI();
        register_tab(STR("Half Online"), [](CppUserModBase* instance) {
            auto* mod = dynamic_cast<HalfOnlineImGui*>(instance);
            if (mod) mod->render();
        });
    }
};

#define HALF_ONLINE_IMGUI_API __declspec(dllexport)
extern "C" {
    HALF_ONLINE_IMGUI_API RC::CppUserModBase* start_mod() { return new HalfOnlineImGui(); }
    HALF_ONLINE_IMGUI_API void uninstall_mod(RC::CppUserModBase* mod) { delete mod; }
}
