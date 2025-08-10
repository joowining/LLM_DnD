use ratatui::{
    layout::{Alignment, Constraint, Direction, Layout, Rect},
    style::{Color, Modifier, Style},
    text::{Line, Span},
    widgets::{Block, Borders, Paragraph, Scrollbar, ScrollbarOrientation, ScrollbarState, Wrap},
    Frame,
};

use crate::app::App;

pub fn ui(f: &mut Frame, app: &mut App) {
    let size = f.size();

    // 전체 레이아웃 구성
    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Length(3),      // 헤더 (program name + 현재 위치)
            Constraint::Min(12),        // 메인 출력 영역 (스크롤 가능)
            Constraint::Length(6),      // 이전 입력 내역
            Constraint::Length(3),      // 사용자 입력
            Constraint::Length(4),      // 사용자 스테이터스/장비
        ])
        .split(size);

    // 각 영역 렌더링
    render_header(f, app, chunks[0]);
    render_main_output_with_scroll(f, app, chunks[1]);
    render_input_history(f, app, chunks[2]);
    render_user_input(f, app, chunks[3]);
    render_status_equipment(f, app, chunks[4]);
}

fn render_header(f: &mut Frame, app: &App, area: Rect) {
    let header_chunks = Layout::default()
        .direction(Direction::Horizontal)
        .constraints([
            Constraint::Percentage(40),
            Constraint::Percentage(60),
        ])
        .split(area);

    // 프로그램 이름
    let title_spans = vec![
        Span::styled("🎲 ", Style::default().fg(Color::Yellow)),
        Span::styled(&app.program_name, Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD)),
    ];
    
    let program_name = Paragraph::new(Line::from(title_spans))
        .block(Block::default().borders(Borders::ALL))
        .alignment(Alignment::Center);
    f.render_widget(program_name, header_chunks[0]);

    // 현재 위치 및 상태
    let status_color = if app.is_python_running {
        Color::Green
    } else {
        Color::Red
    };
    
    let status_spans = vec![
        Span::styled("📍 ", Style::default().fg(Color::Yellow)),
        Span::styled(&app.current_location, Style::default().fg(status_color)),
        if app.is_python_running {
            Span::styled(" ●", Style::default().fg(Color::Green))
        } else {
            Span::styled(" ○", Style::default().fg(Color::Red))
        }
    ];

    let current_location = Paragraph::new(Line::from(status_spans))
        .block(Block::default().borders(Borders::ALL))
        .alignment(Alignment::Left);
    f.render_widget(current_location, header_chunks[1]);
}

fn render_main_output_with_scroll(f: &mut Frame, app: &mut App, area: Rect) {
    // 스크롤 영역을 위한 레이아웃
    let output_chunks = Layout::default()
        .direction(Direction::Horizontal)
        .constraints([
            Constraint::Min(10),    // 텍스트 영역
            Constraint::Length(1),  // 스크롤바 영역
        ])
        .split(area);

    // 메인 텍스트 출력
    let display_text = app.get_display_text();
    
    // 타이핑 중일 때와 일반 상태일 때 다른 스타일 적용
    let (block_style, title, title_style) = if app.is_typing {
        (
            Style::default().fg(Color::Green),
            "📜 게임 진행 중... ⌨️ 타이핑중",
            Style::default().fg(Color::Yellow).add_modifier(Modifier::SLOW_BLINK)
        )
    } else if !app.typing_queue.is_empty() {
        (
            Style::default().fg(Color::Yellow),
            "📜 게임 출력 (메시지 대기중...)",
            Style::default().fg(Color::Yellow)
        )
    } else {
        (
            Style::default().fg(Color::Gray),
            "📜 게임 출력",
            Style::default().fg(Color::Yellow)
        )
    };

    let main_output = Paragraph::new(display_text)
        .block(
            Block::default()
                .borders(Borders::ALL)
                .title(title)
                .title_style(title_style)
                .border_style(block_style)
        )
        .wrap(Wrap { trim: false })
        .style(Style::default().fg(Color::White))
        .scroll((0, 0));

    f.render_widget(main_output, output_chunks[0]);

    let total_lines = app.output_lines.len() +
        if app.is_typing { 1 } else { 0 } + 
        if !app.typing_queue.is_empty() { 1 } else { 0 };

    // 스크롤바 렌더링
    if total_lines > app.max_display_lines {
        let scrollbar = Scrollbar::new(ScrollbarOrientation::VerticalRight)
            .begin_symbol(Some("↑"))
            .end_symbol(Some("↓"))
            .track_symbol(Some("│"))
            .thumb_symbol("█");

        let mut scrollbar_state = ScrollbarState::new(app.output_lines.len())
            .position(app.scroll_offset);

        f.render_stateful_widget(
            scrollbar,
            output_chunks[1],
            &mut scrollbar_state,
        );
    }
}

fn render_input_history(f: &mut Frame, app: &App, area: Rect) {
    let history_text = app.get_input_history_display();
    
    let input_history = Paragraph::new(history_text)
        .block(
            Block::default()
                .borders(Borders::ALL)
                .title("📋 최근 명령어 (최신순)")
                .title_style(Style::default().fg(Color::Cyan))
        )
        .wrap(Wrap { trim: true })
        .style(Style::default().fg(Color::DarkGray));
    
    f.render_widget(input_history, area);
}

fn render_user_input(f: &mut Frame, app: &App, area: Rect) {
    let input_text = if app.current_input.is_empty() {
        if app.is_typing {
            "타이핑 진행 중... (Ctrl+Space: 건너뛰기, Ctrl+1/2/3: 속도조절)"
        } else {
            "명령어를 입력하세요... (Enter: 실행, ↑/↓: 스크롤, ESC/Q: 종료)"
        }
    } else {
        &app.current_input
    };

    let input_style = if app.current_input.is_empty() {
        Style::default().fg(Color::DarkGray)
    } else {
        Style::default().fg(Color::White).bg(Color::Blue)
    };

    let border_color = if app.is_python_running {
        Color::Green
    } else {
        Color::Red
    };

    let title = if app.is_python_running {
        "⌨️  사용자 입력 (준비됨)"
    } else {
        "⌨️  사용자 입력 (연결 끊김)"
    };

    let user_input = Paragraph::new(input_text)
        .block(
            Block::default()
                .borders(Borders::ALL)
                .title(title)
                .title_style(Style::default().fg(Color::Green))
                .border_style(Style::default().fg(border_color))
        )
        .style(input_style);
    
    f.render_widget(user_input, area);
    
    // 커서 위치 표시 (입력 중일 때만)
    if !app.current_input.is_empty() && app.is_python_running {
        // 안전한 문자 단위 커서 위치 계산
        let chars_before_cursor: String = app.current_input
            .chars()
            .take(app.cursor_position)
            .collect();

        let cursor_x = area.x + chars_before_cursor.chars().count() as u16 + 1;
        let cursor_y = area.y + 1;
        
        if cursor_x < area.x + area.width - 1 {
            f.set_cursor(cursor_x, cursor_y);
        }
    }
}

fn render_status_equipment(f: &mut Frame, app: &App, area: Rect) {
    let status_chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Length(2),  // 사용자 상태
            Constraint::Length(2),  // 장비 상태
        ])
        .split(area);

    // 사용자 스테이터스
    let status_spans = vec![
        Span::styled("🏃 ", Style::default().fg(Color::Yellow)),
        Span::styled(&app.user_status, Style::default().fg(Color::White)),
    ];

    let user_status = Paragraph::new(Line::from(status_spans))
        .block(
            Block::default()
                .borders(Borders::TOP | Borders::LEFT | Borders::RIGHT)
                .title("🎭 캐릭터 상태")
                .title_style(Style::default().fg(Color::Magenta))
        );
    f.render_widget(user_status, status_chunks[0]);

    // 장비 상태
    let equipment_spans = vec![
        Span::styled("⚔️ ", Style::default().fg(Color::Yellow)),
        Span::styled(&app.equipment_status, Style::default().fg(Color::White)),
    ];

    let equipment_status = Paragraph::new(Line::from(equipment_spans))
        .block(
            Block::default()
                .borders(Borders::ALL)
                .title("🎒 장비 및 시스템")
                .title_style(Style::default().fg(Color::Blue))
        );
    f.render_widget(equipment_status, status_chunks[1]);
}